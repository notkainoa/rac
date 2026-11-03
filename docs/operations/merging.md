# Merging to main

`main` is protected by the repository ruleset **Protect main**.

## What a merge needs

- **A pull request.** Nobody pushes to `main` directly, and no approval
  is required: PRs are opened under the maintainer's account, and GitHub
  doesn't let an author approve their own PR.
- **Five passing checks:**
  - `Patches apply with Apple's patch` (macOS). It applies the whole
    stack with the release pipeline's `/usr/bin/patch`. Quoted or spaced
    file names fail there and nowhere else
    ([#74](https://github.com/notkainoa/rac/issues/74)).
  - `Patch series`
  - `Patches apply without fuzz`
  - `Python tests`
  - `lint`
- **No force-push and no deletion** of `main`.

The macOS `sanity` and `substitution` jobs still run on every PR but
aren't required, because they queue for a long time. Before merging a
patch change, run `devutils/rac/remote-build.sh verify-series <branch>`,
which reproduces the sanity job's offset and fuzz check on the build Mac
in a few minutes.

## Merging when a check is stuck in the queue

GitHub's macOS runners sometimes queue for hours, which holds
`Patches apply with Apple's patch`. The maintainer, as a repository
admin, can merge a PR anyway:

```sh
gh pr merge <number> --repo notkainoa/rac --merge --admin
```

`--admin` merges past the ruleset, but only through a PR: admins still
can't push to `main` directly. Use it only when every check that has
finished is green and the waiting one is stuck in the queue, not failing.
For a change under `patches/`, run `verify-series` first.

Agents never merge. Only the maintainer does.
