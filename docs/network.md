# What rac connects to

*Draft. The host list below is empty until the first real capture fills it
in.*

rac's promise is that nothing phones home to rac: no telemetry, no accounts,
no ads. This page is the proof for launch gate G10 — not a policy statement
but a recording. The [network capture workflow](../.github/workflows/net-capture.yml)
launches a release build on a throwaway profile, records every host the
browser touches, and diffs the result against the list below. A host that
shows up in the capture but isn't listed fails the job, so this page can't
drift from what the build really does.

## Fresh profile, defaults

AI off, Helium services off, a single fresh window left idle:

```hosts
# TODO: fill in from the first net-capture run (workflow_dispatch,
# services: off). One host or *.wildcard per line, # comments for why rac
# reaches it.
```

One line per host, or `*.example.com`, which covers `example.com` itself and
every subdomain (but not `example.com.evil.net`). The IP addresses sockets
resolve to are not listed; the hostname that produced them is.

Loopback (`localhost`, `127.0.0.1`, `::1`) and Helium's dev-build placeholder
(`*.qjz9zk`, the dead TLD ungoogled-chromium points Google endpoints at) are
recorded by the capture but reported separately — they never belong in this
list.

## How it's captured

`.github/workflows/net-capture.yml` (manual, `workflow_dispatch`) mounts the
DMG from a build run or release the way the install smoke test does, then
launches `rac.app/Contents/MacOS/rac` with:

- `--user-data-dir=<temp>` — a throwaway profile, never a real one
- `--no-default-browser-check`, plus `--no-first-run` unless `first-run`
  asks for a real first launch (see below)
- `--log-net-log=<dir>/netlog.json --net-log-capture-mode=Default`
- `BREAKPAD_DUMP_LOCATION` pointed into the same temp profile

The `first-run` input picks what the launch looks like:

- `skip` (default): `--no-first-run`, which skips rac's welcome tour.
- `onboarding-open`: no `--no-first-run`, so a real first launch shows the
  tour, which stays open for the whole idle.
- `onboarding-closed`: the same, then after about 30 seconds the tour is
  closed without finishing it, as a user does with the red button, and the
  browser idles on the window that opens.

Closing the tour early writes no pref: `helium.completed_onboarding` and
`helium.services.user_consented` stay false, and the tour returns next
launch (only the tour's last step sets `completed_onboarding`). So seeding
prefs cannot reproduce that state, since it would skip the tour. The
tour is a views window that AppleScript can't see, so the capture asks the
browser's DevTools HTTP endpoint (`--remote-debugging-port=0`, loopback
only, reported separately like other loopback traffic) to close its page,
the same path as the page closing itself. If that fails it tries System
Events clicking the window's close button, which needs Accessibility
permission the runner may not grant; if both fail the job records a FAIL
and the run is effectively `onboarding-open`. The job summary names the
mode and the method used. This was not verified on a runner when written.
With `services: on` and a first-run mode, only the consent pref is seeded
(not `completed_onboarding`) so the tour still appears.

No URLs are opened. After `minutes` (default 10) the browser gets SIGTERM,
then SIGKILL if it hasn't exited within 30 seconds (SIGTERM lets Chromium flush the buffered net-log tail) — a killed browser can leave the net-log
truncated, which `devutils/rac/hostlist.py` tolerates by keeping every
complete event. `hostlist.py hosts` turns the events into the sorted host
list (request URLs, DNS lookups, connect jobs, HTTP/2 and QUIC sessions,
WebSockets, proxy resolution), and `hostlist.py compare` fails the job when
a seen host isn't listed above. The net-log and host list are uploaded as
the `net-capture-*` artifact.

## What changes when you turn things on

- **Helium services.** Extension downloads, uBlock filter lists, spell
  check, bangs, and Chromium component updates all run on Helium's servers,
  behind Helium's consent toggle (see
  [internals/overview.md](internals/overview.md#branding-and-helium-services)).
  `services: on` seeds `helium.services.enabled` and
  `helium.services.user_consented` into `Default/Preferences` before launch,
  the same prefs the onboarding toggle sets. TODO: list the service hosts
  here from a `services: on` capture.
- **AI.** Off by default and costs nothing when off — no provider process,
  no requests (see [internals/ai.md](internals/ai.md#ai-off-costs-nothing)).
  Turned on, rac talks only to the provider you configure: your API key's
  endpoint, a local model, or an installed agent's own CLI. There is no
  rac-hosted AI server.
- **Updates.** `rac.browser_updates` is on by default, so the Sparkle check
  may appear even in a default capture: the feed is
  `github.com/notkainoa/rac/releases/latest/download/appcast-<arch>.xml`,
  and GitHub serves release assets from a CDN host
  (`objects.githubusercontent.com` — TODO: confirm the exact host from the
  capture). The check never touches `updates.helium.computer`.
- **Crash reports.** Off. `rac/privacy/disable-crash-uploads.patch` empties
  the upload URL and deletes reports locally, so nothing is ever sent.
- **Sync.** rac has no sync.
- **Extensions.** None installed by default. An extension you add can reach
  its own hosts; that's between you and the extension. TODO: decide whether
  a capture with a bundled default set ever needs a list here.
