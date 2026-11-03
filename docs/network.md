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

Loopback (`localhost`, `127.0.0.1`, `::1`) and Helium's placeholder
(`*.qjz9zk`, the dead TLD ungoogled-chromium points Google endpoints at, in
release builds too) are recorded by the capture but reported separately —
they never belong in this list.

## Seen but never sent

`hostlist.py` lists a host as contacted only if something actually left the
browser for it. A request that stays on the machine goes in a separate
"seen but never sent" section, with the reason, and never fails the diff. A
host that also shows up in an ordinary event counts as contacted.

Before you consent to Helium services, nothing is sent to them. Two entries
still appear in a capture and neither leaves the browser:

- `services.helium.imput.net/bangs.json`, which rac only looks up in its own
  disk cache at startup (`ERR_CACHE_MISS` on a fresh profile), with a
  network-quality check beside it that only reads the in-memory DNS cache.
  Reasons: `cache-only`, `local-only lookup`.
- `helium-services-are-disabled.qjz9zk`, the address Helium gives the
  component updater, extension updates and spellcheck downloads until you
  consent, in release builds too. The browser rewrites it to `trk:` and
  blocks it (`ERR_BLOCKED_BY_CLIENT`) before any DNS lookup or connection.
  Reason: `blocked`.

## How it's captured

`.github/workflows/net-capture.yml` (manual, `workflow_dispatch`) mounts the
DMG from a build run or release the way the install smoke test does, then
launches `rac.app/Contents/MacOS/rac` with:

- `--user-data-dir=<temp>` — a throwaway profile, never a real one
- `--no-first-run --no-default-browser-check`
- `--log-net-log=<dir>/netlog.json --net-log-capture-mode=Default`
- `BREAKPAD_DUMP_LOCATION` pointed into the same temp profile

No URLs are opened. After `minutes` (default 10) the browser gets SIGTERM,
then SIGKILL if it hasn't exited — a killed browser can leave the net-log
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
