# Speed bench (launch gate G11)

`bench.py` compares rac against a Helium release on the same Chromium major,
driving both over the DevTools protocol with throwaway profiles. rac's
promise is "never slower than Helium"; this is the number that proves it.

Everything is the Python standard library — no pip, no node. `cdp.py` is a
minimal WebSocket CDP client; `pages/` holds the local test pages the run
serves itself on 127.0.0.1.

## How to run

```
python3 devutils/rac/bench/bench.py run \
    --app rac=/path/to/rac.app \
    --app helium=/path/to/Helium.app \
    --rounds 10 \
    --out results.json
python3 devutils/rac/bench/bench.py report results.json
python3 devutils/rac/bench/bench.py report results.json --markdown
```

- `--app NAME=PATH` takes the `.app` bundle or the binary inside it, and is
  repeatable. Every app gets byte-identical flags. The report's ratio
  column is the first `rac*` app over the first non-rac one.
- `--warmup N` (default 1) untimed launches per app before the rounds.
- `--pages DIR` overrides the served pages (default: `pages/` here).
- `--idle-seconds` (default 30) is the idle-CPU window; `--settle-seconds`
  (default 2) the quiet time after each memory level.
- Results append to `--out` after every app-round, so an interrupted run
  still has data. A round's browser output log (stdout and stderr together)
  is kept in `<out stem>-logs/` (`results.json` gives `results-logs/`)
  whenever the round reported an error.

Never point the bench at a real profile or an installed copy's app: every
run uses a fresh `--user-data-dir` under the system temp dir, and the
profile dir is refused if its path contains "Application Support".

In CI, `.github/workflows/bench.yml` does all of this on `workflow_dispatch`
from a build `run-id` and a `helium-tag`.

## What happens in a round

One untimed warm-up launch per app comes first (`--warmup`, default 1), so a freshly copied app's
one-time costs (signature checks, cold disk cache) aren't charged to the
app that happens to launch first. Then each round launches every app once,
alternating who goes first (rac, helium; helium, rac; ...) so drift on the
machine and order effects land on both sides. For
each app: fresh temp profile, launch with `--remote-debugging-port=0`,
read the port from `DevToolsActivePort`, measure, SIGTERM then SIGKILL the
whole process tree, delete the profile.

Both apps are launched the same way. rac's `--rac-launch-in-background`
(never activates the app, paints the window as active) is **not** used: it
changes how the window is shown, Helium has no equivalent, and it could skew
launch and frame timings. Run local benches on a machine nobody is using;
in CI there is no foreground to protect. Launch is "fresh profile, warm
binary": the number is not a first-launch-after-reboot measurement.

## The metrics

| metric | what it is | how it's measured |
| --- | --- | --- |
| `cold_launch_ms` | exec → first page loaded and usable | Time from just before spawning the process until the first page target reports `document.readyState === "complete"` — i.e. `Page.loadEventFired` has fired (a page-side promise resolves on `'load'` if it hasn't yet). Includes the bench's own polling (0.1 s steps for the port file, the endpoint and the first page target, so up to roughly 300 ms in total), equal for both apps. Each app's startup page URL is listed in the report: if the two apps start on different pages, the cold-launch numbers compare different work. |
| `devtools_port_ms` | exec → DevTools up | Time until `<profile>/DevToolsActivePort` is readable. A strict subset of cold launch; useful for telling browser-start cost from page-load cost. |
| `new_tab_ms` | CDP target creation → blank tab ready | `Target.createTarget about:blank` → its load event. Measures tab creation plus an empty page, taken at one tab; it is not Cmd+T and not the New Tab page. |
| `tab_switch_ms` | target activation → it paints | `Target.activateTarget` between two loaded local pages (not a user click on the tab strip) → the shown tab's `requestAnimationFrame` resolves through `Runtime.evaluate`. Median of the 5 alternating switches per round. One method for every app: a switch whose rAF never fires is dropped and noted (the median covers the rest; the round has none if all fail), never swapped for a different method. |
| `scroll_ms` | wheel step → scrolled frame | `Input.dispatchMouseEvent` wheel on `long.html` → the page's `scroll` listener ran and painted a frame via rAF. |
| `type_latency_ms` | keypress → input event | `Input.dispatchKeyEvent` `x` into `#t` on `input.html` → the element's `input` listener ran. Timed from the bench's side, from just before the `keyDown` call to the return of the `Runtime.evaluate` that waits for the in-page flag, so it includes the `keyDown` round trip and the evaluate round trip (two CDP calls, not one); that overhead is the same for both apps. |
| `mem_1tab_mb`, `mem_10tab_mb`, `mem_20tab_mb` | RSS with 1/10/20 tabs | Sum of `ps -o rss=` over the whole process tree (`pgrep -P` recursion), which counts pages shared between processes more than once (macOS has no cheap PSS); the same bias applies to both apps. Measured after that level's tabs all loaded plus a settle. Tabs cycle `index.html`/`long.html`/`input.html` on the local server. |
| `idle_cpu_pct` | CPU% while idle | `(cputime_after − cputime_before) / idle window` (`--idle-seconds`, default 30) summed per process over the tree via `ps -o cputime=`, counting only processes alive at both ends, measured with all 20 tabs open and nothing happening. |
| `idle_wakeups` | idle wakeups in the window | Sum of the tree's `IDLEW` column in `top -l 2 -s <idle window>`'s second sample (in `-l` mode, samples after the first are deltas). `powermetrics` would be better but needs root, so it isn't used. |

The report gives, per metric per app: **median (min–max, n)** and the
rac/Helium ratio on medians (the first `rac*` app over the first other app;
`—` when the denominator's median is 0). `run` exits 1 when an app has no
successful cold launch, so a bench where every round failed can't pass as a
comparison. If an app's process tree survives SIGKILL, that round's numbers
are discarded and the run stops, so leftovers can't skew later rounds.

## Interpreting results

- **This bench is noisy on shared machines.** GitHub's free `macos-latest`
  runners are busy VMs: medians of 10 interleaved rounds keep the comparison
  honest, but treat CI numbers as *advisory*. The release gate is one run on
  an idle real Mac.
- A ratio around `1.00` is parity. Something consistently above ~1.1 on a
  latency metric, or meaningfully above 1.0 on memory/wakeups, is what the
  "never slower" promise cares about.
- `idle_wakeups` and `idle_cpu_pct` vary most with the machine's other
  load — they're tree-relative (only the app's own processes), but CPU
  accounting still inherits scheduler noise.
- `tab_switch_ms` measures to the next painted frame, not to "fully
  rendered" — that's the honest part of perceived switch latency.

## What is deliberately not measured

- **Sidebar reveal.** The plan listed it, but the only DevTools-reachable
  trigger is the `helium.browser.zen_mode` pref, which flips zen mode (a
  resize), not the hover/edge reveal users see. Helium has zen mode too, so
  it isn't rac-only either. A number that measures a different thing than
  its name would be worse than none; it needs a native input harness, not
  CDP.

## Files

- `bench.py` — `run` and `report` subcommands, all measurement logic.
- `cdp.py` — minimal stdlib CDP WebSocket client (no Origin header, text
  frames, `call` + `wait_event`).
- `pages/` — `index.html`, `long.html` (scroll), `input.html` (typing `#t`).
- `test_bench.py`, `test_cdp.py` — `python3 -m unittest discover -s
  devutils/rac/bench -p 'test_*.py'`.
- `../../../.github/workflows/bench.yml` — the CI wrapper.
