# CI and release status (2026-10-25)

- All nine release secrets exist (Developer ID .p12, notarization, Sparkle keys).
- PR #16 hardened the release job (fail on missing feeds, pipefail, pin action,
  tag the built commit, removed bump.yml). PR #19 made sccache work with the
  GitHub Actions cache: export ACTIONS_* to run steps, set
  ACTIONS_CACHE_SERVICE_V2=on, SCCACHE_IGNORE_SERVER_IO_ERROR=1.
- Dry-run build 40149762883 (build-only, no release) ran three 5-hour phases per
  architecture and was cancelled in phase 4. Each phase restarted siso at step 0
  and re-fetched everything from cache (96% hit rate in phase 3), finishing only
  ~58k of ~130k steps per phase on x86_64 (remaining: 92,369 → 51,130 → 52,312).
  Upstream Helium has the same reset but its WebDAV sccache is ~3x faster, so it
  finishes in three phases.
- ROOT CAUSE FOUND (2026-10-25, details in /tmp/rac-siso-checkpoint.md): the
  checkpoint tar uses bsdtar's default "restricted pax" format, which drops
  sub-second mtimes for files without xattrs (183,538 of 183,578 files in
  out/Default). siso compares mtimes to the nanosecond, so it reruns nearly
  everything. Fix: `tar --format pax` in github_prepare_artifacts.sh (PR #20,
  about +1% archive size). Reproduced locally. A build-only CI run on that branch
  (run 40222453249) is validating that phase 2 resumes where phase 1 stopped.
- CI never compiles rac's unit tests. "Sanity" applies patches and does a short
  build that passes on timeout.
- Fallback idea (needs maintainer approval): build and sign 0.1.0 locally on the
  maintainer's Mac and publish to the same Sparkle feed.

## Validation run 40222453249 (tar fix, 2026-10-25 to 2026-10-26)

- The pax fix works: no "older than log" reruns; remaining steps shrink each phase.
  x86_64 remaining: 92,352 -> 71,370 -> 60,512 -> 51,425 -> 46,220.
  arm64 remaining: 56,232 -> 43,362 -> 31,802 -> 18,477 -> 3,391 (would have
  finished in phase 6).
- New limit: raw CPU. After phase 1 the sccache hit rate is about 0%, because the
  repo's GitHub Actions cache is capped at 10 GB (in use: 10 GB, about 148k
  entries) and thrashes. Free macos-latest runners compile about one Blink file
  every 6.5 s. x86_64 is much slower because it also builds a host (arm64) copy
  of Blink and content for the V8 context snapshot (clang_arm64_v8_x64).
- Phase 6 died on a flaky artifact download: the 5.36 GB checkpoint "downloaded"
  without sums.txt, the checksum step failed, and fail-fast cancelled arm64 one
  phase from the end. Needs a retry or verification around the download.
- Options for the engineering plan: ship Apple Silicon only first (like Ardia);
  retry the checkpoint download; larger or third-party runners (Helium uses
  sponsored Depot M4 runners and Depot Cache); a self-hosted runner on the
  maintainer's Mac (public repo risk); build, sign, and notarize locally.
