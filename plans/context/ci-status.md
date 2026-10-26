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
