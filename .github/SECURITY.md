# Security

## Reporting a vulnerability

Report security problems privately, using **Report a vulnerability** on
this repo's [Security tab](https://github.com/notkainoa/rac/security). Please
don't open a public issue.

Include what's affected, how to reproduce it, and the rac version.

## What belongs where

rac is built from Chromium, ungoogled-chromium, and Helium. Most browser
security bugs come from those projects.

- **A bug in rac's own changes** (anything under `patches/rac/`, or behavior
  that only exists in rac): report it here.
- **A bug that also happens in Chromium or Google Chrome:** report it to
  [Chromium](https://www.chromium.org/Home/chromium-security/reporting-security-bugs/).
- **Not sure:** report it here, and the maintainer will route it.

rac picks up Chromium security fixes by syncing with Helium releases.

## Supported versions

Only the latest rac release gets security fixes.
