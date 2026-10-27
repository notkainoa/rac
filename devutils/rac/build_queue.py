#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Shares one Mac's builds between the agents working on it.

Every local build goes through this queue instead of a bare `he build`, so a
16 GB Mac never runs more than two builds at once. See
docs/operations/worktrees.md#the-build-queue.

usage: devutils/rac/build-queue.sh [options] <command> [args...]
       devutils/rac/build-queue.sh status
       devutils/rac/build-queue.sh log [lines]

  he build            runs `he build` from this checkout's dev.sh
  --run               takes a run slot (harness, eval, `worktree.sh run`)
                      instead of a build slot; `worktree.sh run` does this
                      on its own
  --full NOTE         a full build that the maintainer approved (D6). It
                      takes both build slots and has no step cap. NOTE says
                      which approval, e.g. "D6 item 2: sync cold build"
  --priority          sync and launch-gate work: goes ahead of other waiters
  --max-steps N       stop the build if it shows more than N steps
                      (default 20000)
  --allow-main        allow building in the main checkout

There are two build slots and two run slots. A slot is a directory under
~/.rac-build-queue made with mkdir, which is atomic. Waiters are served first
come, first served, with priority waiters first. A slot whose holder died is
freed. The manual lock (~/.rac-build-queue/manual) holds both build slots.
The queue refuses to start a build below 20 GB of free disk, and waits while
memory pressure is critical.
"""

from pathlib import Path
import argparse
import datetime
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time

BUILD_SLOTS = ('build-1', 'build-2')
RUN_SLOTS = ('run-1', 'run-2')
MANUAL = 'manual'
WAITING = 'waiting'
MUTEX = '.mutex'
LOG = 'queue.log'
HOLDER = 'holder.json'
DEFAULT_MAX_STEPS = 20000
# siso and ninja progress lines start with [done/total].
PROGRESS = re.compile(rb'^\[\s*([\d,]+)\s*/\s*([\d,]+)\s*\]')
# kern.memorystatus_vm_pressure_level: 1 normal, 2 warning, 4 critical.
PRESSURE_NAMES = {1: 'normal', 2: 'warning', 4: 'critical'}
PRESSURE_CRITICAL = 4
# Exit codes of the queue itself, distinct from the build's own.
EXIT_REFUSED = 75
EXIT_STEP_CAP = 76


def state_dir():
    return Path(os.environ.get('RAC_BUILD_QUEUE_DIR',
                               Path.home() / '.rac-build-queue'))


def poll_seconds():
    return float(os.environ.get('RAC_BUILD_QUEUE_POLL', '3'))


def min_free_gb():
    return float(os.environ.get('RAC_BUILD_QUEUE_MIN_FREE_GB', '20'))


def say(message):
    print(f'build queue: {message}', file=sys.stderr, flush=True)


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


def log_event(event, **fields):
    line = json.dumps({'time': now(), 'event': event, **fields})
    with open(state_dir() / LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def group_alive(pgid):
    if not pgid:
        return False
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def write_json(path, data):
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(data, indent=1) + '\n', encoding='utf-8')
    tmp.replace(path)


class Mutex:
    """A short-lived lock around every change to the queue's state."""

    STALE_SECONDS = 30

    def __enter__(self):
        path = state_dir() / MUTEX
        while True:
            try:
                path.mkdir()
                return self
            except FileExistsError:
                try:
                    age = time.time() - path.stat().st_mtime
                except FileNotFoundError:
                    continue
                if age > self.STALE_SECONDS:
                    # Its holder died inside the lock, which takes milliseconds.
                    try:
                        path.rmdir()
                    except OSError:
                        pass
                time.sleep(0.02)

    def __exit__(self, *exc):
        try:
            (state_dir() / MUTEX).rmdir()
        except FileNotFoundError:
            pass


def holder_alive(holder):
    return holder is not None and (alive(holder.get('pid'))
                                   or group_alive(holder.get('pgid')))


def reap():
    """Frees slots and tickets whose process died. Call inside the mutex."""
    root = state_dir()
    for name in BUILD_SLOTS + RUN_SLOTS:
        slot = root / name
        if not slot.is_dir():
            continue
        holder = read_json(slot / HOLDER)
        if holder is None:
            # A holder writes its file inside the mutex, so this is a slot
            # left by a crash between mkdir and write. Give it a moment.
            if time.time() - slot.stat().st_mtime < Mutex.STALE_SECONDS:
                continue
        elif holder_alive(holder):
            continue
        shutil.rmtree(slot, ignore_errors=True)
        log_event('reap', slot=name, holder=holder)
    for ticket in sorted((root / WAITING).glob('*.json')):
        data = read_json(ticket)
        if data is None or not alive(data.get('pid')):
            ticket.unlink(missing_ok=True)


def tickets(pool):
    """Waiting tickets for a pool, in the order they will be served."""
    found = []
    for path in sorted((state_dir() / WAITING).glob('*.json')):
        data = read_json(path)
        if data and data.get('pool') == pool:
            found.append((path, data))
    return found


def next_ticket_name(priority):
    root = state_dir()
    counter = root / 'seq'
    try:
        seq = int(counter.read_text()) + 1
    except (OSError, ValueError):
        seq = 1
    counter.write_text(str(seq))
    # Priority tickets sort first; within a level, by arrival.
    return f'{0 if priority else 1}-{seq:09d}.json'


def untracked_builds(holders):
    """Running siso builds that didn't come through the queue."""
    worktrees = [h.get('worktree') for h in holders if h and h.get('worktree')]
    try:
        out = subprocess.run(['ps', '-axo', 'pid=,command='],
                             capture_output=True, text=True,
                             check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    found = []
    for line in out.splitlines():
        pid, _, command = line.strip().partition(' ')
        if '/third_party/siso/' not in command or ' ninja' not in command:
            continue
        if any(command.find(w + '/') >= 0 for w in worktrees):
            continue
        found.append({'pid': int(pid), 'command': command})
    return found


def slot_holders(names):
    root = state_dir()
    return {name: read_json(root / name / HOLDER)
            for name in names if (root / name).is_dir()}


def free_slots(pool):
    """Names of the slots in a pool that a new holder may take."""
    root = state_dir()
    if pool == 'run':
        return [n for n in RUN_SLOTS if not (root / n).exists()]
    if (root / MANUAL).exists():
        return []
    free = [n for n in BUILD_SLOTS if not (root / n).exists()]
    # A bare `he build` running outside the queue still uses a slot's worth
    # of the Mac.
    held = slot_holders(BUILD_SLOTS)
    extra = len(untracked_builds(list(held.values())))
    return free[:max(0, len(free) - extra)]


def free_disk_gb(path):
    return shutil.disk_usage(path).free / 1e9


def memory_pressure():
    fake = os.environ.get('_RAC_BUILD_QUEUE_PRESSURE')
    if fake:
        return int(fake)
    try:
        out = subprocess.run(['sysctl', '-n', 'kern.memorystatus_vm_pressure_level'],
                             capture_output=True, text=True, check=True).stdout
        return int(out.strip())
    except (OSError, ValueError, subprocess.CalledProcessError):
        return 1


def git_info(cwd):
    def git(*args):
        result = subprocess.run(['git', '-C', str(cwd), *args],
                                capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else ''

    top = git('rev-parse', '--show-toplevel')
    branch = git('branch', '--show-current') or git('rev-parse', '--short', 'HEAD')
    main = ''
    listing = git('worktree', 'list', '--porcelain')
    if listing:
        main = listing.splitlines()[0].removeprefix('worktree ')
    resolve = lambda p: str(Path(p).resolve()) if p else ''
    return resolve(top), branch, resolve(main)


def is_run_command(command):
    return (any(Path(arg).name == 'worktree.sh' for arg in command)
            and 'run' in command)


def resolve_command(command, worktree):
    """Turns `he ...` into a call to this checkout's dev.sh."""
    if command[0] != 'he':
        return command
    dev_sh = Path(worktree or os.getcwd()) / 'dev.sh'
    if not dev_sh.is_file():
        raise SystemExit(f'build queue: no dev.sh at {dev_sh}')
    # dev.sh finds the checkout from $0, which zsh sets to the sourced file.
    return ['zsh', '-c', 'source "$0" && he "$@"', str(dev_sh), *command[1:]]


class Queue:

    def __init__(self, args, command):
        self.args = args
        self.command = command
        self.pool = 'run' if args.run else 'build'
        self.need = 2 if args.full else 1
        self.ticket = None
        self.slots = []
        self.child = None
        self.worktree, self.branch, self.main = git_info(Path.cwd())
        self.info = {
            'pid': os.getpid(),
            'pgid': None,
            'worktree': self.worktree or os.getcwd(),
            'branch': self.branch,
            'kind': 'full' if args.full else self.pool,
            'note': args.full or '',
            'priority': bool(args.priority),
            'command': ' '.join(command),
        }

    def check_disk(self):
        if self.pool != 'build':
            return
        free = free_disk_gb(self.info['worktree'])
        if free < min_free_gb():
            log_event('refuse', reason='disk', free_gb=round(free, 1), **self.info)
            say(f'refusing: {free:.1f} GB free, under the {min_free_gb():.0f} GB floor. '
                'Free disk space (ask the maintainer before deleting a worktree), '
                'then queue again.')
            raise SystemExit(EXIT_REFUSED)

    def wait_for_slots(self):
        root = state_dir()
        with Mutex():
            self.ticket = root / WAITING / next_ticket_name(self.args.priority)
            write_json(self.ticket, {**self.info, 'pool': self.pool,
                                     'need': self.need, 'since': now()})
        log_event('wait', **self.info)
        last_note = 0.0
        while True:
            note = None
            with Mutex():
                reap()
                waiting = tickets(self.pool)
                head = waiting and waiting[0][0] == self.ticket
                if head:
                    pressure = memory_pressure()
                    free = free_slots(self.pool)
                    if pressure >= PRESSURE_CRITICAL:
                        note = 'memory pressure is critical; waiting for it to drop'
                    elif len(free) >= self.need:
                        self.check_disk()
                        self.take(free[:self.need])
                        return
                    else:
                        note = 'next in line; waiting for a slot'
                else:
                    order = [path for path, _ in waiting]
                    position = order.index(self.ticket) + 1 if self.ticket in order else '?'
                    note = f'waiting, number {position} in line'
            if time.time() - last_note > 60:
                say(f'{note} (see: devutils/rac/build-queue.sh status)')
                last_note = time.time()
            time.sleep(poll_seconds())

    def take(self, names):
        """Takes free slots. Call inside the mutex."""
        root = state_dir()
        for name in names:
            (root / name).mkdir()
            self.slots.append(name)
            write_json(root / name / HOLDER, {**self.info, 'started': now()})
        self.ticket.unlink(missing_ok=True)
        self.ticket = None
        log_event('start', slots=names, **self.info)
        say(f'got {", ".join(names)}; running: {self.info["command"]}')

    def update_holders(self):
        with Mutex():
            for name in self.slots:
                path = state_dir() / name / HOLDER
                data = read_json(path) or {}
                data.update(pgid=self.info['pgid'])
                write_json(path, data)

    def release(self, status, reason):
        with Mutex():
            for name in self.slots:
                path = state_dir() / name
                holder = read_json(path / HOLDER)
                if holder and holder.get('pid') == os.getpid():
                    shutil.rmtree(path, ignore_errors=True)
            if self.ticket:
                self.ticket.unlink(missing_ok=True)
        if self.slots or reason != 'done':
            log_event('end', slots=self.slots, status=status, reason=reason,
                      **self.info)
        self.slots = []
        self.ticket = None

    def stop_child(self, sig=signal.SIGTERM):
        if not self.child or self.child.poll() is not None:
            return
        try:
            os.killpg(self.child.pid, sig)
            self.child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(self.child.pid, signal.SIGKILL)
            self.child.wait()
        except ProcessLookupError:
            pass

    def run_child(self):
        command = resolve_command(self.command, self.worktree)
        if self.pool == 'run':
            self.child = subprocess.Popen(command, start_new_session=True)
            self.info['pgid'] = self.child.pid
            self.update_holders()
            return self.child.wait(), 'done'

        self.child = subprocess.Popen(command, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT,
                                      start_new_session=True)
        self.info['pgid'] = self.child.pid
        self.update_holders()
        cap = None if self.args.full else self.args.max_steps
        out = sys.stdout.buffer
        for line in self.child.stdout:
            out.write(line)
            out.flush()
            match = PROGRESS.match(line)
            if cap is None or not match:
                continue
            total = int(match.group(2).replace(b',', b''))
            if total > cap:
                say(f'stopping: this build shows {total:,} steps, over the '
                    f'{cap:,} cap. Something invalidated the tree (see '
                    'docs/operations/worktrees.md). A full build needs the '
                    "maintainer's approval; if it has it, queue again with "
                    '--full "<approval>".')
                log_event('cap', steps=total, cap=cap, **self.info)
                self.stop_child()
                return EXIT_STEP_CAP, 'step cap'
        return self.child.wait(), 'done'

    def run(self):
        self.check_disk()
        def on_signal(signum, frame):
            raise KeyboardInterrupt(signum)
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, on_signal)
        status, reason = 1, 'error'
        try:
            self.wait_for_slots()
            status, reason = self.run_child()
        except KeyboardInterrupt:
            status, reason = 130, 'interrupted'
            self.stop_child()
        except SystemExit as e:
            status, reason = e.code, 'refused'
            raise
        finally:
            self.release(status, reason)
        return status


def fmt_age(iso):
    try:
        then = datetime.datetime.fromisoformat(iso)
    except (TypeError, ValueError):
        return '?'
    seconds = int((datetime.datetime.now().astimezone() - then).total_seconds())
    hours, rest = divmod(seconds, 3600)
    return f'{hours}h{rest // 60:02d}m' if hours else f'{rest // 60}m{rest % 60:02d}s'


def describe(h):
    where = h.get('branch') or h.get('worktree', '?')
    note = f' [{h["note"]}]' if h.get('note') else ''
    prio = ' priority' if h.get('priority') else ''
    return (f'pid {h.get("pid")}  {h.get("kind")}{prio}  {where}  '
            f'({h.get("worktree")})  {h.get("command")}{note}')


def status():
    root = state_dir()
    with Mutex():
        reap()
    pressure = memory_pressure()
    print(f'rac build queue ({root})')
    print(f'  disk free {free_disk_gb(Path.home()):.0f} GB, memory pressure '
          f'{PRESSURE_NAMES.get(pressure, pressure)}')
    manual = root / MANUAL
    if manual.exists():
        print(f'  manual lock held for {fmt_age(datetime.datetime.fromtimestamp(manual.stat().st_mtime).astimezone().isoformat())}'
              ' (both build slots)')
    holders = []
    for name in BUILD_SLOTS + RUN_SLOTS:
        holder = read_json(root / name / HOLDER) if (root / name).is_dir() else None
        if holder:
            holders.append(holder)
            print(f'  {name:8} {fmt_age(holder.get("started"))}  {describe(holder)}')
        else:
            print(f'  {name:8} free')
    for build in untracked_builds(holders):
        print(f'  outside the queue: pid {build["pid"]}  {build["command"][:120]}')
    for pool in ('build', 'run'):
        waiting = tickets(pool)
        if waiting:
            print(f'  waiting for a {pool} slot:')
            for i, (_, t) in enumerate(waiting, 1):
                need = ' (needs both slots)' if t.get('need') == 2 else ''
                print(f'    {i}. waited {fmt_age(t.get("since"))}  {describe(t)}{need}')
    return 0


def show_log(lines):
    path = state_dir() / LOG
    if not path.exists():
        return 0
    for line in path.read_text(encoding='utf-8').splitlines()[-lines:]:
        e = json.loads(line)
        extra = ''
        if e['event'] == 'start':
            extra = ' ' + ','.join(e.get('slots', []))
        elif e['event'] == 'end':
            extra = f' {",".join(e.get("slots", []))} status {e.get("status")} ({e.get("reason")})'
        elif e['event'] == 'cap':
            extra = f' {e.get("steps"):,} steps > {e.get("cap"):,}'
        elif e['event'] == 'refuse':
            extra = f' {e.get("reason")} {e.get("free_gb")} GB'
        elif e['event'] == 'reap':
            extra = f' {e.get("slot")}'
        who = e.get('branch') or (e.get('holder') or {}).get('branch', '')
        print(f'{e["time"]}  {e["event"]:6}{extra}  pid {e.get("pid", "")}  '
              f'{e.get("kind", "")}  {who}  {e.get("command", "")}')
    return 0


def main(argv):
    parser = argparse.ArgumentParser(
        prog='build-queue.sh', usage=__doc__.split('\n\n')[2].removeprefix('usage: '),
        add_help=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--full', metavar='NOTE')
    parser.add_argument('--priority', action='store_true')
    parser.add_argument('--max-steps', type=int, default=DEFAULT_MAX_STEPS)
    parser.add_argument('--allow-main', action='store_true')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    root = state_dir()
    (root / WAITING).mkdir(parents=True, exist_ok=True)

    if not args.command:
        parser.error('give a command, such as: he build')
    if args.command == ['status']:
        return status()
    if args.command[0] == 'log':
        return show_log(int(args.command[1]) if len(args.command) > 1 else 40)
    if args.full is not None and not args.full.strip():
        parser.error('--full needs a note naming the approval, e.g. "D6 item 2"')
    if args.run and args.full:
        parser.error('--run and --full do not go together')
    if is_run_command(args.command):
        args.run = True

    queue = Queue(args, args.command)
    if (queue.pool == 'build' and not args.allow_main and queue.main
            and queue.worktree == queue.main):
        say('refusing to build in the main checkout; build in a worktree '
            '(AGENTS.md), or pass --allow-main if the maintainer asked')
        return EXIT_REFUSED
    return queue.run()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
