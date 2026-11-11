# Feature worktrees

Each feature can live in its own git worktree with its own Chromium build
tree. You can work on several features at once and test each one separately.

A full build tree is over 100 GB and takes hours to build. A worktree doesn't
copy it. It gets an APFS copy-on-write clone of the main checkout's built
tree, which takes about 30 seconds and almost no disk space until files
change. The first build in a new worktree takes a minute or two. After that,
builds only redo what the feature's patches change.

## The main checkout is the base

Every new worktree clones `build/src` from the main checkout. Keep that tree
built and matching `main`, and do feature work in worktrees instead.

Setup refuses to clone while a build is running in the main checkout.

## Creating a worktree

In the Factory App, create a new worktree and pick the **rac feature tree**
setup profile. It comes from `.factory/worktree-setups/rac.yaml`.

Without Factory:

```sh
git worktree add -b feat/<name> <path> main
cd <path>
devutils/rac/worktree.sh setup
```

Setup checks out the Helium submodule from the main checkout, merges the
patches, clones the build tree, points it at the new worktree, and applies
any patches that differ from the main checkout's. To clone another
checkout's build tree instead, such as a worktree that's newer than the
main checkout, pass it: `devutils/rac/worktree.sh setup <checkout>`. gn
needs Xcode, so setup uses `/Applications/Xcode.app` when `xcode-select`
points at the Command Line Tools. Like every `sync`, it also
applies rac's names to the dev tree (see
[Branding](../internals/overview.md#branding-and-helium-services)).

## Working in a worktree

- Build with `devutils/rac/build-queue.sh he build`. See
  [the build queue](#the-build-queue).
- Run with `devutils/rac/worktree.sh run`, not `he run`. `he run` uses
  one shared dev profile. If two builds launch with the same profile, the
  second one only opens a window in the browser that's already running.
  `run` gives each worktree its own profile in `build/profile`. Extra
  flags pass through, including `--rac-window-screenshot=/path.png` for
  an in-process PNG of the window (needed on macOS 26). Agents attach
  those screenshots when the work is done; they don't hand first look
  to the maintainer.
- Make patches with the quilt workflow in
  [overview.md](../internals/overview.md#making-a-rac-change). Commit after
  `he unmerge`, then run `he merge` to keep working.
- After the branch's patches change outside quilt, such as after a rebase or
  a `git pull`, run `devutils/rac/worktree.sh sync`, then build through
  the queue.
  Sync stops, and names the file, if popping a patch would throw away an
  edit that isn't saved in any version of it, applied or committed. It
  prints the `quilt diff` that shows the edit. Before you `quilt refresh`
  to keep it, check the patch's `git log -p`: if a rebase or pull changed
  the patch, a refresh would undo that change. To throw the edit away, run
  `devutils/rac/worktree.sh sync --discard`.

If a build in a worktree shows tens of thousands of steps, something
invalidated the clone. Stop it and find out why before letting it run for
hours.

## The build queue

Several agents share each Mac, and a 16 GB Mac swaps hard with more than two
Chromium builds at once. So every local build goes through
`devutils/rac/build-queue.sh` instead of a bare `he build`:

```sh
devutils/rac/build-queue.sh he build     # waits for a slot, builds, frees it
devutils/rac/build-queue.sh status       # who holds a slot, who waits
devutils/rac/build-queue.sh log          # recent starts, ends, and refusals
```

- **Slots.** Each Mac has two build slots and two run slots, as directories
  under `~/.rac-build-queue/`. Screenshot-harness and eval runs take a run
  slot with `--run`. `build-queue.sh devutils/rac/worktree.sh run` picks a
  run slot without it; `worktree.sh run` on its own doesn't queue. A slot is
  freed when its build ends, fails, or is interrupted. If the queue process
  dies, its slot stays held until its build has stopped too, and then the
  next queue user frees it.
- **Order.** First come, first served. Sync and launch-gate work may pass
  `--priority` to go ahead of other waiters.
- **Full builds.** A full build the maintainer approved takes both build
  slots: `build-queue.sh --full "D6 item 2: sync cold build" he build`.
- **File descriptors.** `--pass-fds 3,4` hands open file descriptors to
  the command, for `--remote-debugging-pipe`. Pass the descriptors to
  `build-queue.sh` itself as inheritable fds (Python
  `subprocess.Popen(..., pass_fds=(r, w))`, or bash `3<&$r 4>&$w`), since
  non-inheritable fds don't survive into the queue. The queue drops its
  own copies once the command starts, so pipe EOF still means the command
  closed its end.
- **Guards.** The queue refuses to start a build with less than 20 GB free,
  and waits while memory pressure is critical. It stops a build that shows
  more than 20,000 steps, since that means something invalidated the tree.
  siso's total starts near the whole graph and shrinks as it finds steps up
  to date, so the queue judges it only after it settles (three minutes, or
  a minute without changing), or once 20,000 steps have actually run. It
  refuses to build in the main checkout without `--allow-main`, and refuses
  a second build in a worktree that's already building.
- **Batches.** Don't build after every edit. Collect a batch of changes,
  build once, then run every test and screenshot the batch needs. Never
  hold a slot while you think or fix; let the build end and queue again.
- **Outside builds.** A siso build that didn't come through the queue
  doesn't hold a slot, but the queue leaves one build slot empty for each
  one, and `status` lists them.
- **The manual lock.** `mkdir ~/.rac-build-queue/manual` holds both build
  slots until you `rmdir` it, and waiters print how long it has been held.
  It predates the queue and only works one way: whoever holds it can't see
  builds in the queue. Use it only when the queue itself is broken.

## Building on the MacBook Pro

`devutils/rac/remote-build.sh` moves Chromium compiles and screenshot
launches to the maintainer's MacBook Pro over ssh; threads, git, and
reviews stay on the Air. Everything on the Pro lives in `~/rac-remote`:
the bare `rac.git` and `helium-chromium.git`, a `base/` the Pro clones
and cold-builds itself (the Air→Pro link can't carry a built tree), one
clone per worktree in `wt/<name>`, the queue's state, and `logs/`.
`setup-host` runs once and reports both Macs' Xcode and SDK, which need
not match.

`build-base <ref>` clones a GitHub ref into `base/` and bootstraps it:
`he presetup`, `he merge`, an explicit `quilt push -a --fuzz 0` (never
`he push`, whose `--refresh` rewrites patches; `worktree.sh sync` needs
the `.pc` state it makes), `worktree.sh sync`, then `he configure`. Each
phase prints a timestamped heartbeat, also kept in `logs/bootstrap.log`,
and a bootstrap that stopped picks up where it stopped on a rerun. A base
already bootstrapped at the ref is adopted untouched; one holding a tree
for another ref is refused, never moved or recloned. Only
`--approved "<who/when>"` (or `--resume --approved` later) queues the
cold build, detached; it refuses while a build of the base is already
queued or running. Follow it with `status` and `log`.

The base's toolchain is recorded once in `base/.rac-toolchain`, and each
clone keeps a copy in its `build/`. `push`, `build`, `run`, and
`--resume` refuse when the Pro's Xcode or SDK drifts from it, since a
build then recompiles all of Chromium. `push` a committed worktree to its
clone (a new clone waits for the base's finished build; `--seed <clone>`
clones another idle, built clone's tree instead, such as one closer to
the branch), `build` it
through the queue under `nice` with four cores left free,
`run -- --rac-window-screenshot=x.png` for a background browser with its
own profile (the shot lands in the clone's `build/shots/`), `evals` for
the agent-safety eval suite (see [below](#agent-evals-on-the-pro)), and
`pull` files back. Nobody builds rac natively on the Pro: every build
there goes through `remote-build.sh`. An Xcode update on a build machine
invalidates every tree built there (new compiler flags and SDK path), so
keep Xcode pinned on build machines; `build`, `run` and `push` refuse when
the Pro's Xcode differs from the one its base recorded.

After pushing a patch change to GitHub and before asking for a merge, run
`devutils/rac/remote-build.sh verify-series <your branch>`. It reproduces
the macOS CI sanity job's check, which the fast Linux checks can't: the
Pro fetches the branch, makes a throwaway clone `wt/verify-<branch>` from
the base's tree, and, holding one build slot, pops the whole stack and
pushes it again with `--fuzz 0`. It fails on a patch that doesn't apply
and names every hunk that applied with an offset or fuzz, either of which
turns main red. The push log stays in `logs/verify-<branch>.log`, and the
clone is removed afterwards unless `--keep` is given. It never builds.

### What a remote run may do

A remote run launches the clone's built binary directly — never
`worktree.sh run`, whose `--enable-ui-devtools` would open a full
UI-control WebSocket — with `--user-data-dir` at the clone's throwaway
`build/profile`, `--use-mock-keychain`,
`--disable-features=DialMediaRouteProvider`, and
`--rac-launch-in-background`. After `--`, args are a fixed allowlist:

- `--no-first-run`, `--rac-launch-in-background`,
  `--force-prefers-reduced-motion`, `--rac-force-increased-contrast`,
  `--disable-backgrounding-occluded-windows`.
- `--rac-import-arc-now` (only with `--rac-import-source-root=`),
  `--rac-import-arc-undo-now` (undoes the clone profile's own Arc import
  at startup, reading no Arc data; alone or with
  `--rac-import-source-root=`),
  `--rac-arc-import-fixture=<path>` and `--rac-import-source-root=<path>`,
  Arc import inputs that must exist inside the clone. Any of these four
  makes it an Arc import run: it launches without `--test-type` (the
  sign-ins import `CHECK`s that the switch is absent), and in its place
  gets no network at all. Every request, loopback included, goes to a
  dead proxy, so nothing an import run opens or clicks can reach a page
  that offers a PWA install. It also refuses `--test-type`, `--serve`,
  the PWA commands and http(s) URLs. A run with neither input still
  gets `--rac-import-source-root=` an empty `build/empty-import-root`
  the Pro makes in the clone, because a `setup?arc` tab restored from
  the clone's session, or the tour's Arc step, would otherwise read the
  Pro's real Arc. That root doesn't make it an import run, and it
  doesn't count as the import input that opening `chrome://setup` or
  Settings > General needs.
- `--rac-window-screenshot=<name>.png` and
  `--rac-window-screenshot-delay=<1-4 digits>`, in seconds and shorter
  than the run's `--timeout`; the shot lands in
  `build/shots/`.
- `--log-net-log=<name>.json` and `--rac-frame-log=<name>.log`; the logs
  land in `build/logs/`, never in `build/profile`. A run with a net log
  ends by sending SIGTERM to the browser's main process alone and giving
  it 10 seconds to quit cleanly, which flushes the log; stopping the
  whole process group at once kills the network service first.
- `--net-log-capture-mode=Default|IncludeSensitive|Everything`,
  `--enable-logging=stderr`, `--vmodule=<spec>`,
  `--rac-force-color-mode=light|dark|system`.
- `--window-size=W,H`, each 400 to 4000, for taller or wider windows.
- `--test-type`, bare (no value). Every remote run launches with it
  anyway, so passing it changes nothing; it's accepted so PWA scripts
  can say what they rely on. Chromium's test mode makes
  `AppShimCreationAndLaunchDisabledForTest()` true
  (`chrome/browser/web_applications/os_integration/mac/web_app_shortcut_mac.mm`),
  so no PWA install, from a command or from a page's own install
  button, writes an app shim into the Pro's `~/Applications`. It opens
  no debugging port and no file access.
- A bare arg is a URL and gets the same allowlist `open-urls` gets:
  loopback and test hosts, the named internal pages, `about:blank`, and
  `@SERVE@/<path>` with `--serve`. A `chrome://` or `rac://` page given
  this way may not open: a profile that has tabs restores them instead.
  Open internal pages with the requests file's `open-urls` verb, which
  always opens a new tab.

Three `run` options change the clone before launch:

- `--layout sidebar|top-bar` writes the clone profile's
  `rac.browser.layout` (0 or 1) into `Default/Preferences`. A fresh
  profile starts with the top bar (`top-bar-default.patch`), so
  `--layout sidebar` is the one to pass for the other half. It gets the
  same symlink and inside-the-clone checks the downloads prefs get. It
  refuses while a browser from the clone runs, since that browser
  already read its prefs.
- `--no-profile-picker` writes `profile.show_picker_on_startup = false`
  into the clone profile's `Local State`: the profile picker's "Show on
  startup" checkbox, off (`chrome/browser/ui/profiles/profile_picker.cc`).
  A clone with several profiles then restores them at launch instead of
  waiting on the picker, which a run can't click. Nothing else in Local
  State changes, and it refuses while a browser from the clone runs.
- `--serve DIR` serves a folder in the clone on 127.0.0.1 at a port the
  kernel picks, for this run only. `@SERVE@` at the start of a URL arg
  or an `open-urls` URL becomes `http://127.0.0.1:PORT`; only a plain
  path may follow it, so it can't name another host or port, and it's
  refused without `--serve`. DIR must be relative, stay inside the
  clone once symlinks resolve, sit outside `build/`, and hold no
  symlinks. Responses carry a Content-Security-Policy that keeps the
  page's network fetches, scripts, frames and forms on that server
  (inline scripts, `data:` and `blob:` still work). A CSP can't stop a
  page from navigating its own tab, so a `--serve` run's browser also
  sends every request to a dead loopback proxy (`--proxy-server=
  http://127.0.0.1:9`; loopback is bypassed, so the server still
  answers) and keeps WebRTC from sending UDP around it. Nothing a served
  page does reaches another host. The server stops when the run ends,
  however it ends.

The requests file a run feeds the screenshot harness is one checked
line. Pages and command ids are allowlists. rac's own ids are limited to
40800 to 40803 (the command bar, with and without the current URL,
clear tabs, the little window); 40804, copy as Markdown, writes the
Mac's clipboard. `command 40002` (install as a PWA) and `command 34055`
(open in an app window) need `--test-type` in the same run. A run that opens
`chrome://setup` (or `chrome://setup?arc`, the tour's Arc import step)
needs an import input in the same run. Typed text is plain words only (ASCII letters, digits, spaces, `-`, `_`), and a script
that types may not also move the caret or click — at most one
`key return`, after the last `type`. A run that opens a settings page
(the only allowed ones are `settings/assistant`, `settings/appearance`,
`settings/privacy`, `settings/system/shortcuts`, and `settings/general`,
which also needs an import
input because of its Arc import card) may take screenshots, scroll and
zoom only, so its requests file may send no input except `wheel X Y DY`
and the zoom commands (`command 38001`, `38002`, `38003`). Zoom out to
fit a card the window is too short for: macOS caps the window at the
screen's height.

Known limits: import-input paths are checked with `inside_clone`
before launch, but a path swapped for a symlink between the check and the
browser reading it isn't caught — accepted, since our own agents write
the scripts. The same goes for a symlink added to a `--serve` folder
after the check. The served pages' policy doesn't cover top-level
navigation, so a page's own script could still navigate the tab
elsewhere. A `sandbox-exec` profile for remote runs is the planned
longer-term fix.

### Agent evals on the Pro

`evals <worktree>` runs Core's agent-safety eval runner
(`devutils/rac/evals/run.py`, stdlib Python) against the clone's built
browser. The runner is reviewed code fetched from a branch, not an
agent-written script — that is why this verb alone may hand the browser a
remote-debugging port. The verb fetches `--ref`'s branch (default
`feat/agent-evals`) from the rac repo's GitHub URL into the bare
`~/rac-remote/rac.git`, extracts only the `devutils/rac/evals` subtree
into a fresh `~/rac-remote/evals/<clone>` (one per clone, so two clones'
evals can't clobber each other), and runs it from there with `python3 -I`
under one run slot held for the whole eval (`--timeout`, 1 to 14400s,
default 3600s, queue wait included). The clone must have a built browser
and no browser from it running.

The runner starts its own servers on 127.0.0.1 and launches
`build/src/out/Default/rac.app/Contents/MacOS/rac` directly — never
`worktree.sh run`, no UI DevTools, no `--remote-allow-origins` — with a
throwaway profile under the clone's `build/` (its `TMPDIR` is
`build/evals/tmp`), one launch at a time, killing each before the next.
Core owns that side of the runner. `RAC_EVALS_NO_QUEUE=1` keeps it from
taking a second queue slot for those launches, and the verb's allowlist
after `--` (`--gate`, `--keep-profile`, `--screenshots`, `--list`,
`--variants=<ids>`, `--host-mode=names|loopback`) is all that reaches it. When the runner
ends, fails, times out, or is interrupted, the verb kills its process
group and every browser from the clone, then exits with the runner's own
status.

Results land in the clone's `build/evals/results`, and `--screenshots`
PNGs in `build/evals/results/shots` (old `*.json` and `*.png` there are
cleared first). Fetch them with:

```sh
devutils/rac/remote-build.sh pull <worktree> build/evals/results <local dir>
```

## Updating the base

After merging features into `main`, update the main checkout so new
worktrees start from it:

```sh
he unmerge
git pull
he merge
devutils/rac/worktree.sh sync
devutils/rac/build-queue.sh --allow-main he build
```

`sync` pops only the patches that changed, plus every patch applied after
them, and then applies the new versions. A change to a late rac patch
rebuilds a few files. A change to an early Helium patch can rebuild most of
Chromium.

Existing worktrees don't follow the base on their own. To bring one up to
date, run `he unmerge`, rebase its branch onto `main`, run `he merge`, then
`sync` and build through the queue.

## Removing a worktree

Cleanup (`devutils/rac/worktree.sh cleanup`, run by the Factory profile)
stops any build or browser running from the worktree. It then moves
`build/` into the main checkout's `build/.trash/` and deletes it in the
background. Setup and cleanup also clear trees left there by an interrupted
delete.

Git refuses `git worktree remove` without `--force` because the worktree
contains the Helium submodule. Factory won't remove these worktrees
automatically either, because the merged patches count as untracked files.
Delete them yourself when the feature is done.

## How the clone is made usable

A cloned tree still refers to the main checkout in three places. Setup fixes
each one:

- **Siso's file state** (`out/Default/.siso_fs_state`) is keyed by absolute
  path. Without it, siso treats every step as dirty and rebuilds all of
  Chromium. Setup exports the state with `siso fs export`, rewrites the
  paths, and imports it back.
- **GN's build files** contain absolute paths for a few rules, such as
  Helium's onboarding page and uBlock. Setup reruns `gn gen`. Those rules
  then rerun once, which explains most of the 46 steps in the first build.
- **Quilt** records the patches folder in `.pc/.quilt_patches`. Setup points
  it at the worktree's `patches/`.

`sync` relies on `build/src/.pc/.rac_applied`, which records a hash of each
applied patch, and on a copy of each applied version in
`.pc/.rac_patch_bytes/`. The hashes tell it which patch files changed since
they were applied. The copies let it replay a patch that's about to be
popped and check that its files hold nothing else. Don't delete them to get
past a refusal; that loses the edit sync is protecting.
