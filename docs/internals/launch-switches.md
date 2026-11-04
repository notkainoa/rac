# Launch switches and planted profiles

Every rac user data dir shares one Keychain key ("rac Safe Storage").
So anyone who can launch rac as the user with
`--user-data-dir=<their dir>` can plant the real profile's files there,
as hard links or copies, and rac decrypts them with the real key. Two
patches narrow what such a launch gives away:

- `rac/devtools/refuse-debug-doors.patch` (#63): a launch that asks for
  `--remote-debugging-port` or `--remote-debugging-pipe` off the default
  profile runs on the mock keychain, so the planted files don't decrypt.
- `rac/devtools/refuse-profile-read-switches.patch` (#65): release builds
  drop the switches that would hand the decrypted data to another
  program:
  - extension and app loading: `--load-extension`,
    `--disable-extensions-except`, `--load-apps` and
    `--load-and-launch-app`;
  - full-capture net logs: `--net-log-capture-mode` unless it's `Default`
    or `HeavilyRedacted`;
  - TLS key logs: `--ssl-key-log-file` and the `SSLKEYLOGFILE` variable;
  - certificate bypasses: `--ignore-certificate-errors` and
    `--ignore-certificate-errors-spki-list`.

  Dev builds (`RAC_DEV_SWITCHES`) keep them all. The hook runs in
  `ChromeMainDelegate::PostEarlyInitialization`, before the process
  singleton forwards the command line to a running rac and before
  anything reads these switches. Moving it later reopens the gap.
  `--proxy-server` stays allowed, because people use it legitimately. On
  its own it only sees encrypted traffic; the certificate and key-log
  switches are what made it dangerous.

## Accepted limits

These patches don't stop a planted profile. They remove the cheapest ways
to read one. What's left is accepted for launch, because an attacker who
can start rac with their own arguments already runs code as the user.
That code can read the user's files directly, or ask the Keychain for the
key.

- **Forged settings.** Chromium signs sensitive preferences, such as which
  extensions are installed and their permissions, with a seed that only
  Google-branded builds ship (`chrome_pref_service_factory.cc`). In rac
  the seed is empty. A planted profile can therefore carry its own
  `Secure Preferences`, and rac loads an unpacked extension the attacker
  wrote into it, with no switch at all. Fixing this needs a per-install
  secret seed, which is tracked as post-launch work (#115).
- **Anything else that reads the profile from inside the browser.** For
  example, an extension the user installed themselves. The shared key is
  the root cause, and these patches don't change it.
