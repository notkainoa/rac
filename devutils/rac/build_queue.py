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
  --run               takes a run slot (harness, eval) instead of a build
                      slot. `build-queue.sh devutils/rac/worktree.sh run`
                      picks a run slot without it
  --full NOTE         a full build that the maintainer approved (D6). It
                      takes both build slots and has no step cap. NOTE says
                      which approval, e.g. "D6 item 2: sync cold build"
  --priority          sync and launch-gate work: goes ahead of other waiters
  --max-steps N       stop the build if it shows more than N steps
                      (default 20000)
  --allow-main        allow building in the main checkout
  --pass-fds N[,N...] hands open file descriptors to the command, e.g.
                      --pass-fds 3,4 for --remote-debugging-pipe. The fds
                      must reach build-queue.sh itself as inheritable
                      descriptors (subprocess.Popen(..., pass_fds=(r, w)),
                      or bash `3<&$r 4>&$w`), since non-inheritable fds
                      don't survive into the queue. The queue drops its
                      own copies once the command starts, so the caller
                      still sees EOF when the command closes its end.

There are two build slots and two run slots. A slot is a directory under
~/.rac-build-queue holding holder.json and a lock file that its queue process
keeps locked (flock) while it lives. Waiters are served first come, first
served, with priority waiters first. A slot whose queue process and build
both died is freed. The manual lock (~/.rac-build-queue/manual) holds both
build slots. The queue refuses to start a build below 20 GB of free disk,
and waits while memory pressure is critical.
"""

from pathlib import Path
import argparse
import datetime
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

BUILD_SLOTS = ('build-1', 'build-2')
RUN_SLOTS = ('run-1', 'run-2')
MANUAL = 'manual'
WAITING = 'waiting'
# The first version of this script used a `.mutex` directory. A file with
# that name would make a still-running first-version queue spin forever at
# release, so the lock file has its own name.
MUTEX = '.mutex.lock'
LOG = 'queue.log'
HOLDER = 'holder.json'
LOCK = 'lock'
SIGNALS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
DEFAULT_MAX_STEPS = 20000
# siso and ninja progress lines start with [done/total]; siso then prints its
# elapsed time, e.g. `[153/55790] 47.80s F CXX obj/...`.
PROGRESS = re.compile(rb'^\[\s*([\d,]+)\s*/\s*([\d,]+)\s*\](?:\s+(\S+))?')
GO_DURATION = re.compile(r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?')
# siso's total is every step minus those it has found up to date so far, so
# it starts near the whole graph and shrinks. Trust it as the build's size
# only once it has settled: after this much siso time, or after it has stayed
# within STABLE_FRACTION for STABLE_SECONDS.
SETTLE_SECONDS = 180
STABLE_SECONDS = 60
STABLE_FRACTION = 0.01
# A siso build: the executable is siso and its first argument is ninja.
# depot_tools runs it under caffeinate too, which this doesn't match.
SISO_NINJA = re.compile(r'^(?:\S*/)?siso\s+ninja(?:\s|$)')
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


def stop_grace():
    """Seconds a stopped build gets to exit before it is killed."""
    return float(os.environ.get('RAC_BUILD_QUEUE_STOP_GRACE', '15'))


def say(message):
    try:
        print(f'build queue: {message}', file=sys.stderr, flush=True)
    except OSError:
        pass


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


def log_event(event, **fields):
    line = json.dumps({'time': now(), 'event': event, **fields})
    with open(state_dir() / LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


class Interrupted(BaseException):
    """SIGINT, SIGTERM, or SIGHUP arrived."""

    def __init__(self, signum):
        super().__init__(signum)
        self.signum = signum


class _Signals:
    # While depth > 0, a signal is held until the section ends, so a slot or
    # child is never half set up when the queue stops.
    depth = 0
    pending = None


def on_signal(signum, frame):
    if _Signals.depth:
        _Signals.pending = _Signals.pending or signum
        return
    raise Interrupted(signum)


def defer_signals():
    _Signals.depth += 1


def resume_signals():
    _Signals.depth -= 1
    if not _Signals.depth and _Signals.pending:
        signum, _Signals.pending = _Signals.pending, None
        raise Interrupted(signum)


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
    if not pgid or pgid <= 1:
        return False
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def try_lock(path, create=False):
    """Opens and locks path without waiting.

    Returns the open fd, or None if another process holds the lock. The
    kernel drops the lock when the fd's process dies.
    """
    fd = os.open(path, os.O_RDWR | (os.O_CREAT if create else 0), 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None
    except BaseException:
        os.close(fd)
        raise
    return fd


def lock_held(path):
    """True if a live process holds path's lock, None if there's no file."""
    try:
        fd = try_lock(path)
    except FileNotFoundError:
        return None
    if fd is None:
        return True
    os.close(fd)
    return False


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_json(path, data):
    tmp = path.with_name(f'{path.name}.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(data, indent=1) + '\n', encoding='utf-8')
    tmp.replace(path)


class Mutex:
    """A short-lived lock around every change to the queue's state.

    One fd per process, so taking it again after an interrupted section
    can't deadlock against this process's own lock.
    """

    _fd = None
    _path = None
    _depth = 0

    def __enter__(self):
        cls = Mutex
        if not cls._depth:
            path = state_dir() / MUTEX
            if cls._path != path:
                if cls._fd is not None:
                    os.close(cls._fd)
                    cls._fd = None
                cls._fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
                cls._path = path
            # Waiting here stays interruptible; the section itself doesn't.
            fcntl.flock(cls._fd, fcntl.LOCK_EX)
        defer_signals()
        cls._depth += 1
        return self

    def __exit__(self, *exc):
        cls = Mutex
        cls._depth -= 1
        if not cls._depth:
            fcntl.flock(cls._fd, fcntl.LOCK_UN)
        resume_signals()


def slot_state(slot):
    """Returns (holder, state) for a slot directory.

    state is 'held' (its queue process lives), 'orphan' (the queue process
    is gone but its build still runs), 'starting', or 'dead'.
    """
    holder = read_json(slot / HOLDER)
    held = lock_held(slot / LOCK)
    if held:
        return holder, 'held'
    if holder is None:
        if held is None:
            # No lock and no holder: a first-version slot between mkdir and
            # write, or a crash there. Give it a moment.
            try:
                age = time.time() - slot.stat().st_mtime
            except FileNotFoundError:
                return None, 'dead'
            if age < 30:
                return None, 'starting'
        return None, 'dead'
    # Slots from the first version have no lock file; trust their pid.
    if held is None and alive(holder.get('pid')):
        return holder, 'held'
    if group_alive(holder.get('pgid')):
        return holder, 'orphan'
    return holder, 'dead'


def slots(names):
    """(name, holder, state) for each taken slot among names."""
    root = state_dir()
    found = []
    for name in names:
        if (root / name).is_dir():
            found.append((name, *slot_state(root / name)))
    return found


def ticket_alive(path, data):
    held = lock_held(path.with_suffix('.lock'))
    if held is not None:
        return held
    return data is not None and alive(data.get('pid'))


def reap():
    """Frees slots and tickets whose process died. Call inside the mutex."""
    root = state_dir()
    for name, holder, state in slots(BUILD_SLOTS + RUN_SLOTS):
        if state == 'dead':
            shutil.rmtree(root / name, ignore_errors=True)
            log_event('reap', slot=name, holder=holder)
    waiting = root / WAITING
    for ticket in sorted(waiting.glob('*.json')):
        if not ticket_alive(ticket, read_json(ticket)):
            ticket.unlink(missing_ok=True)
            ticket.with_suffix('.lock').unlink(missing_ok=True)
    for lock in waiting.glob('*.lock'):
        if not lock.with_suffix('.json').exists() and not lock_held(lock):
            lock.unlink(missing_ok=True)


def tickets(pool):
    """Waiting tickets for a pool, in the order they will be served."""
    found = []
    for path in sorted((state_dir() / WAITING).glob('*.json')):
        data = read_json(path)
        if data and data.get('pool') == pool:
            found.append((path, data))
    return found


def next_ticket_name(priority):
    """A new ticket name. Call inside the mutex."""
    root = state_dir()
    counter = root / 'seq'
    try:
        seq = int(counter.read_text())
    except (OSError, ValueError):
        seq = 0
    while True:
        seq += 1
        if not any((root / WAITING / f'{p}-{seq:09d}.json').exists()
                   for p in (0, 1)):
            break
    tmp = counter.with_name(f'seq.{os.getpid()}.tmp')
    tmp.write_text(str(seq))
    tmp.replace(counter)
    # Priority tickets sort first; within a level, by arrival.
    return f'{0 if priority else 1}-{seq:09d}.json'


def process_list():
    """`ps` output with pid and command. Tests set _RAC_BUILD_QUEUE_PS."""
    fake = os.environ.get('_RAC_BUILD_QUEUE_PS')
    if fake is not None:
        return fake
    try:
        return subprocess.run(['ps', '-axww', '-o', 'pid=,command='],
                              capture_output=True, text=True, check=True,
                              timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return ''


def untracked_builds(worktrees):
    """siso builds that didn't come through the queue, one per out dir.

    Builds under a slot holder's worktree belong to that holder.
    """
    real = lambda p: os.path.realpath(p).rstrip('/') + '/'
    roots = [real(w) for w in worktrees if w]
    found = {}
    for line in process_list().splitlines():
        pid, _, command = line.strip().partition(' ')
        command = command.strip()
        if not pid.isdigit() or not SISO_NINJA.match(command):
            continue
        args = command.split()
        out = None
        for i, arg in enumerate(args):
            if arg == '-C' and i + 1 < len(args):
                out = args[i + 1]
                break
            if arg.startswith('-C') and len(arg) > 2:
                out = arg[2:]
                break
        if out and any(real(out).startswith(r) for r in roots):
            continue
        found.setdefault(out or command,
                         {'pid': int(pid), 'out': out, 'command': command})
    return list(found.values())


def live_worktrees(taken):
    return [h.get('worktree') for _, h, state in taken
            if h and state in ('held', 'orphan')]


def free_slots(pool):
    """Names of the slots in a pool that a new holder may take."""
    root = state_dir()
    if pool == 'run':
        return [n for n in RUN_SLOTS if not (root / n).exists()]
    if (root / MANUAL).exists():
        return []
    free = [n for n in BUILD_SLOTS if not (root / n).exists()]
    if not free:
        return free
    # A siso build running outside the queue doesn't hold a slot, but it uses
    # a slot's worth of the Mac, so leave one empty for it.
    worktrees = live_worktrees(slots(BUILD_SLOTS + RUN_SLOTS))
    extra = len(untracked_builds(worktrees))
    return free[:max(0, len(free) - extra)]


def manual_note():
    path = state_dir() / MANUAL
    try:
        since = path.stat().st_mtime
    except FileNotFoundError:
        return ''
    age = fmt_seconds(time.time() - since)
    return (f'the manual lock {path} has held both build slots for {age}. '
            'Whoever made it removes it with `rmdir` when their build ends; '
            'if it looks forgotten, ask the maintainer')


def free_disk_gb(path):
    return shutil.disk_usage(path).free / 1e9


def memory_pressure():
    fake = os.environ.get('_RAC_BUILD_QUEUE_PRESSURE')
    if fake:
        return int(fake)
    try:
        out = subprocess.run(['sysctl', '-n', 'kern.memorystatus_vm_pressure_level'],
                             capture_output=True, text=True, check=True,
                             timeout=5).stdout
        return int(out.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return 1


def git_info(cwd):
    def git(*args):
        try:
            result = subprocess.run(['git', '-C', str(cwd), *args],
                                    capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return ''
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
    """Turns `he ...` into a call to this checkout's dev.sh, or None."""
    if command[0] != 'he':
        return command
    dev_sh = Path(worktree or os.getcwd()) / 'dev.sh'
    if not dev_sh.is_file():
        return None
    # dev.sh finds the checkout from $0, which zsh sets to the sourced file.
    return ['zsh', '-c', 'source "$0" && he "$@"', str(dev_sh), *command[1:]]


def parse_elapsed(token):
    """Seconds from siso's elapsed field (`47.80s`, `1m2.5s`, `850ms`)."""
    if not token:
        return None
    text = token.decode('ascii', 'replace')
    try:
        if text.endswith('ms'):
            return float(text[:-2]) / 1000
        match = GO_DURATION.fullmatch(text)
        if not match or not any(match.groups()):
            return None
        hours, minutes, seconds = match.groups()
        return int(hours or 0) * 3600 + int(minutes or 0) * 60 + float(seconds or 0)
    except ValueError:
        return None


class StepCap:
    """Decides when a build's progress shows it is too big to be incremental."""

    def __init__(self, cap, clock=time.monotonic):
        self.cap = cap
        self.clock = clock
        self.start = clock()
        self.ref = None
        self.ref_at = None

    def check(self, line):
        """Returns why the build should stop after this line, or None."""
        match = PROGRESS.match(line)
        if not match:
            return None
        done = int(match.group(1).replace(b',', b''))
        total = int(match.group(2).replace(b',', b''))
        if done > self.cap:
            return f'this build has already run {done:,} steps, over the {self.cap:,} cap'
        at = parse_elapsed(match.group(3))
        if at is None:
            at = self.clock() - self.start
        if (self.ref is None or at < self.ref_at
                or abs(total - self.ref) > self.ref * STABLE_FRACTION):
            self.ref, self.ref_at = total, at
        settled = at >= SETTLE_SECONDS or at - self.ref_at >= STABLE_SECONDS
        if settled and total > self.cap:
            return f'this build shows {total:,} steps, over the {self.cap:,} cap'
        return None


def descendants(root):
    """(pid, pgid) of every process under root, by walking parent pids."""
    try:
        out = subprocess.run(['ps', '-axo', 'pid=,ppid=,pgid='],
                             capture_output=True, text=True, check=True,
                             timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    children = {}
    for line in out.splitlines():
        try:
            pid, ppid, pgid = (int(f) for f in line.split())
        except ValueError:
            continue
        children.setdefault(ppid, []).append((pid, pgid))
    found = set()
    stack = [root]
    while stack:
        for child in children.get(stack.pop(), []):
            if child not in found:
                found.add(child)
                stack.append(child[0])
    return found


def exit_status(returncode):
    """A shell-style status: a child killed by signal n gives 128 + n."""
    return returncode if returncode >= 0 else 128 - returncode


def silence_stdout():
    """Points stdout at /dev/null after its reader went away (`| head`)."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    os.close(devnull)


class Queue:

    def __init__(self, args, command, resolved, git):
        self.args = args
        self.resolved = resolved
        self.pool = 'run' if args.run else 'build'
        self.need = 2 if args.full else 1
        self.ticket = None
        self.ticket_fd = None
        self.slots = []
        self.slot_fds = []
        self.child = None
        self.reader = None
        self.done = threading.Event()
        self.cap_reason = None
        self.worktree, self.branch, self.main = git
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

    def check_worktree(self, with_tickets):
        """Refuses a second build in a worktree. Call inside the mutex."""
        if self.pool != 'build':
            return
        mine = self.info['worktree']
        others = [h for _, h, state in slots(BUILD_SLOTS)
                  if h and state in ('held', 'orphan')]
        if with_tickets:
            others += [t for path, t in tickets('build') if path != self.ticket]
        for other in others:
            if other.get('worktree') == mine:
                log_event('refuse', reason='worktree busy', **self.info)
                say(f'refusing: pid {other.get("pid")} is already building in '
                    f'{mine} ({other.get("command")}). Wait for it to end '
                    '(see: devutils/rac/build-queue.sh status).')
                raise SystemExit(EXIT_REFUSED)

    def enqueue(self):
        root = state_dir()
        with Mutex():
            reap()
            self.check_worktree(with_tickets=True)
            ticket = root / WAITING / next_ticket_name(self.args.priority)
            self.ticket_fd = try_lock(ticket.with_suffix('.lock'), create=True)
            self.ticket = ticket
            self.ticket_data = {**self.info, 'pool': self.pool,
                                'need': self.need, 'since': now()}
            write_json(ticket, self.ticket_data)
        log_event('wait', **self.info)

    def drop_ticket(self):
        if self.ticket:
            self.ticket.unlink(missing_ok=True)
            self.ticket.with_suffix('.lock').unlink(missing_ok=True)
            self.ticket = None
        if self.ticket_fd is not None:
            os.close(self.ticket_fd)
            self.ticket_fd = None

    def wait_for_slots(self):
        self.enqueue()
        last_note, last_text = 0.0, None
        while True:
            with Mutex():
                reap()
                if not self.ticket.exists():
                    write_json(self.ticket, self.ticket_data)
                order = [path for path, _ in tickets(self.pool)]
                if order and order[0] == self.ticket:
                    pressure = memory_pressure()
                    free = free_slots(self.pool)
                    if pressure >= PRESSURE_CRITICAL:
                        note = 'memory pressure is critical; waiting for it to drop'
                    elif len(free) >= self.need:
                        self.check_disk()
                        self.check_worktree(with_tickets=False)
                        self.take(free[:self.need])
                        return
                    else:
                        note = 'next in line; waiting for a slot'
                else:
                    position = order.index(self.ticket) + 1 if self.ticket in order else '?'
                    note = f'waiting, number {position} in line'
                manual = manual_note() if self.pool == 'build' else ''
            if manual:
                note = f'{note}; {manual}'
            if note != last_text or time.time() - last_note > 60:
                say(f'{note} (see: devutils/rac/build-queue.sh status)')
                last_note, last_text = time.time(), note
            time.sleep(poll_seconds())

    def take(self, names):
        """Takes free slots. Call inside the mutex."""
        root = state_dir()
        for name in names:
            slot = root / name
            slot.mkdir()
            self.slots.append(name)
            self.slot_fds.append(try_lock(slot / LOCK, create=True))
            write_json(slot / HOLDER, {**self.info, 'started': now()})
        self.drop_ticket()
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
                if holder is None or holder.get('pid') == os.getpid():
                    shutil.rmtree(path, ignore_errors=True)
            for fd in self.slot_fds:
                if fd is not None:
                    os.close(fd)
            self.slot_fds = []
            self.drop_ticket()
        if self.slots or reason != 'done':
            log_event('end', slots=self.slots, status=status, reason=reason,
                      **self.info)
        self.slots = []

    def pump(self):
        """Copies the build's output and watches its progress.

        Runs until the output ends, including while the build is stopped, so
        the build never blocks on a full pipe.
        """
        out = sys.stdout.buffer
        cap = None if self.args.full else StepCap(self.args.max_steps)
        with self.child.stdout:
            for line in self.child.stdout:
                if out is not None:
                    try:
                        out.write(line)
                        out.flush()
                    except OSError:
                        out = None
                        silence_stdout()
                if cap and self.cap_reason is None:
                    reason = cap.check(line)
                    if reason:
                        self.cap_reason = reason
                        self.done.set()
        self.done.set()

    def run_child(self):
        piped = self.pool == 'build'
        # pass_fds hands the caller's descriptors (e.g. a debugging pipe)
        # to the command. The queue's lock files stay out: os.open makes
        # them non-inheritable.
        defer_signals()
        try:
            self.child = subprocess.Popen(
                self.resolved, start_new_session=True,
                stdout=subprocess.PIPE if piped else None,
                stderr=subprocess.STDOUT if piped else None,
                pass_fds=self.args.pass_fds)
            # The child has its own copies now; drop the queue's so a
            # caller waiting on the other end sees EOF when the child
            # closes them or exits, not only when this queue ends.
            for fd in self.args.pass_fds:
                os.close(fd)
            self.info['pgid'] = self.child.pid
            self.update_holders()
            if piped:
                self.reader = threading.Thread(target=self.pump, daemon=True)
                self.reader.start()
        except OSError as e:
            say(f'cannot run {self.info["command"]}: {e}')
            return 127 if isinstance(e, FileNotFoundError) else 126, 'error'
        finally:
            # A signal that arrived meanwhile stops the child from here on.
            resume_signals()
        # The reader sets done at the step cap or end of output; poll for
        # the exit in case a leftover process keeps the output open.
        while not self.done.wait(1):
            if self.child.poll() is not None:
                break
        if self.cap_reason and self.child.poll() is None:
            say(f'stopping: {self.cap_reason}. Something invalidated the tree '
                '(see docs/operations/worktrees.md). A full build needs the '
                "maintainer's approval; if it has it, queue again with "
                '--full "<approval>".')
            log_event('cap', reason=self.cap_reason, cap=self.args.max_steps,
                      **self.info)
            self.stop_child()
            return EXIT_STEP_CAP, 'step cap'
        return exit_status(self.child.wait()), 'done'

    def stop_child(self):
        """Stops the build's whole process tree and waits until it's gone."""
        child = self.child
        if child is None:
            return
        pgid = child.pid
        if child.poll() is not None and not group_alive(pgid):
            self.join_reader()
            return
        # siso runs its helper and local commands in their own process
        # groups, so find them by parent pid before their parents exit.
        family = descendants(child.pid)
        self.signal_tree(signal.SIGTERM, pgid, family)
        if not self.wait_gone(pgid, family, stop_grace()):
            family |= descendants(child.pid)
            say('the build did not stop; killing it')
            self.signal_tree(signal.SIGKILL, pgid, family)
            if not self.wait_gone(pgid, family, 10):
                left = sorted(p for p, _ in family if alive(p))
                say(f'warning: build processes still running: {left}')
        self.join_reader()

    def join_reader(self):
        if self.reader:
            self.reader.join(timeout=5)

    @staticmethod
    def signal_tree(sig, pgid, family):
        mine = {os.getpid(), os.getpgrp()}
        for group in {pgid} | {g for _, g in family}:
            if group > 1 and group not in mine:
                try:
                    os.killpg(group, sig)
                except (ProcessLookupError, PermissionError):
                    pass
        for pid, _ in family:
            if pid > 1 and pid not in mine:
                try:
                    os.kill(pid, sig)
                except (ProcessLookupError, PermissionError):
                    pass

    def wait_gone(self, pgid, family, timeout):
        end = time.monotonic() + timeout
        while True:
            self.child.poll()
            if not group_alive(pgid) and not any(alive(p) for p, _ in family):
                return True
            if time.monotonic() >= end:
                return False
            time.sleep(0.1)

    def run(self):
        for sig in SIGNALS:
            signal.signal(sig, on_signal)
        status, reason = 1, 'error'
        try:
            self.check_disk()
            self.wait_for_slots()
            status, reason = self.run_child()
        except Interrupted as e:
            status, reason = 128 + e.signum, 'interrupted'
            say('interrupted; stopping the build')
        except SystemExit as e:
            status, reason = e.code, 'refused'
            raise
        finally:
            # Whatever ended the run, the build stops before its slot frees.
            for sig in SIGNALS:
                signal.signal(sig, lambda signum, frame: None)
            try:
                self.stop_child()
            finally:
                self.release(status, reason)
        return status


def fmt_seconds(seconds):
    seconds = max(0, int(seconds))
    hours, rest = divmod(seconds, 3600)
    return f'{hours}h{rest // 60:02d}m' if hours else f'{rest // 60}m{rest % 60:02d}s'


def fmt_age(iso):
    try:
        then = datetime.datetime.fromisoformat(iso)
    except (TypeError, ValueError):
        return '?'
    return fmt_seconds((datetime.datetime.now().astimezone() - then).total_seconds())


def describe(h):
    where = h.get('branch') or h.get('worktree', '?')
    note = f' [{h["note"]}]' if h.get('note') else ''
    prio = ' priority' if h.get('priority') else ''
    command = ' '.join(str(h.get('command')).split())
    if len(command) > 120:
        command = command[:117] + '...'
    return (f'pid {h.get("pid")}  {h.get("kind")}{prio}  {where}  '
            f'({h.get("worktree")})  {command}{note}')


STATE_NOTES = {
    'held': '',
    'orphan': '  (queue process gone; its build is still running)',
    'starting': '  (starting)',
    'dead': '  (holder gone; the next queue user frees it)',
}


def status():
    """Prints the queue. Changes nothing."""
    root = state_dir()
    taken, waiting = [], {'build': [], 'run': []}
    if root.is_dir():
        with Mutex():
            taken = slots(BUILD_SLOTS + RUN_SLOTS)
            for pool in waiting:
                waiting[pool] = [t for path, t in tickets(pool)
                                 if ticket_alive(path, t)]
    here = git_info(Path.cwd())[0] or os.getcwd()
    pressure = memory_pressure()
    print(f'rac build queue ({root})')
    print(f'  disk free {free_disk_gb(here):.0f} GB (on the volume of {here}), '
          f'memory pressure {PRESSURE_NAMES.get(pressure, pressure)}')
    if (root / MANUAL).exists():
        print(f'  {manual_note()}')
    by_name = {name: (holder, state) for name, holder, state in taken}
    for name in BUILD_SLOTS + RUN_SLOTS:
        holder, state = by_name.get(name, (None, None))
        if holder:
            print(f'  {name:8} {fmt_age(holder.get("started"))}  '
                  f'{describe(holder)}{STATE_NOTES[state]}')
        elif state:
            print(f'  {name:8} taken{STATE_NOTES[state]}')
        else:
            print(f'  {name:8} free')
    for build in untracked_builds(live_worktrees(taken)):
        print(f'  outside the queue: pid {build["pid"]}  '
              f'{build["out"] or build["command"][:120]}')
    for pool, found in waiting.items():
        if found:
            print(f'  waiting for a {pool} slot:')
            for i, t in enumerate(found, 1):
                need = ' (needs both slots)' if t.get('need') == 2 else ''
                print(f'    {i}. waited {fmt_age(t.get("since"))}  {describe(t)}{need}')
    return 0


def fmt_num(value):
    return f'{value:,}' if isinstance(value, int) else str(value)


def show_log(lines):
    path = state_dir() / LOG
    if not path.exists():
        return 0
    text = path.read_text(encoding='utf-8', errors='replace')
    for raw in text.splitlines()[-lines:]:
        try:
            e = json.loads(raw)
        except ValueError:
            e = None
        if not isinstance(e, dict):
            print(f'(unreadable line) {raw[:200]}')
            continue
        event = e.get('event', '?')
        extra = ''
        if event == 'start':
            extra = ' ' + ','.join(map(str, e.get('slots') or []))
        elif event == 'end':
            extra = (f' {",".join(map(str, e.get("slots") or []))} '
                     f'status {e.get("status")} ({e.get("reason")})')
        elif event == 'cap':
            extra = f' {e["reason"]}' if e.get('reason') else (
                f' {fmt_num(e.get("steps"))} steps > {fmt_num(e.get("cap"))}')
        elif event == 'refuse':
            extra = f' {e.get("reason")}'
            if e.get('free_gb') is not None:
                extra += f' {e.get("free_gb")} GB'
        elif event == 'reap':
            extra = f' {e.get("slot")}'
        holder = e.get('holder') if isinstance(e.get('holder'), dict) else {}
        who = e.get('branch') or holder.get('branch', '')
        print(f'{e.get("time", "?")}  {event:6}{extra}  pid {e.get("pid", "")}  '
              f'{e.get("kind", "")}  {who}  {e.get("command", "")}')
    return 0


def parse_pass_fds(text):
    """Fd numbers from --pass-fds, checked against this process."""
    fds = []
    for token in text.split(','):
        token = token.strip()
        try:
            fd = int(token)
        except ValueError:
            raise ValueError(f'{token!r} is not a file descriptor number')
        if fd < 3:
            raise ValueError(f'{fd} is a standard stream; pass fds 3 and above')
        try:
            os.fstat(fd)
        except (OSError, OverflowError):
            raise ValueError(f'{fd} is not open in this process')
        if fd not in fds:
            fds.append(fd)
    return tuple(fds)


def main(argv):
    parser = argparse.ArgumentParser(
        prog='build-queue.sh', usage=__doc__.split('\n\n')[2].removeprefix('usage: '),
        add_help=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--full', metavar='NOTE')
    parser.add_argument('--priority', action='store_true')
    parser.add_argument('--max-steps', type=int, default=DEFAULT_MAX_STEPS)
    parser.add_argument('--allow-main', action='store_true')
    parser.add_argument('--pass-fds', metavar='N[,N...]', default='')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    if not args.command:
        parser.error('give a command, such as: he build')
    if args.command == ['status']:
        return status()
    if args.command[0] == 'log':
        rest = args.command[1:]
        if len(rest) > 1 or (rest and (not rest[0].isdigit() or int(rest[0]) < 1)):
            parser.error('usage: build-queue.sh log [lines], lines a positive number')
        return show_log(int(rest[0]) if rest else 40)
    if args.full is not None and not args.full.strip():
        parser.error('--full needs a note naming the approval, e.g. "D6 item 2"')
    if args.max_steps <= 0:
        parser.error('--max-steps needs a positive number')
    try:
        args.pass_fds = parse_pass_fds(args.pass_fds) if args.pass_fds else ()
    except ValueError as e:
        parser.error(f'--pass-fds: {e}')
    if is_run_command(args.command):
        args.run = True
    if args.run and args.full is not None:
        parser.error('--full is for builds; a run command takes a run slot')
    if args.run and args.command[:2] == ['he', 'build']:
        parser.error('he build needs a build slot; drop --run')

    git = git_info(Path.cwd())
    worktree, _, main_checkout = git
    if (not args.run and not args.allow_main and main_checkout
            and worktree == main_checkout):
        say('refusing to build in the main checkout; build in a worktree '
            '(AGENTS.md), or pass --allow-main if the maintainer asked')
        return EXIT_REFUSED
    resolved = resolve_command(args.command, worktree)
    if resolved is None:
        say(f'refusing: no dev.sh at {Path(worktree or os.getcwd()) / "dev.sh"}; '
            'run `he` commands from a rac checkout')
        return EXIT_REFUSED

    (state_dir() / WAITING).mkdir(parents=True, exist_ok=True)
    return Queue(args, args.command, resolved, git).run()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
