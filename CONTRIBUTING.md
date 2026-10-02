# Contributing to rac

Thanks for wanting to help. rac is mainly built and used by one maintainer,
but contributions are welcome. Anyone can open a pull request, and the
maintainer decides when reviewing it.

## Before you start

- **Read the [vision](VISION.md).** rac is opinionated. A well-built change
  that goes against the vision, such as adding many settings, collecting
  data, or slowing the browser down, won't be merged.
- **Check the [roadmap](docs/roadmap.md)** and existing issues, in case
  someone is already working on it.
- **For big changes, consider opening an issue first** to talk it through.
  You don't have to, but it's the best way to avoid building something that
  won't fit.

## Where to report what

- **Bugs in rac:** open an issue in this repo.
- **Ideas:** open a feature request issue.
- **Questions or anything else:** open a blank issue.
- **Security problems:** report them privately. See
  [SECURITY.md](.github/SECURITY.md).
- **Never report rac issues to Helium.** rac isn't affiliated with Helium.
  If a bug also happens in an unmodified Helium, it probably comes from
  upstream. Mention that in your rac issue, and the maintainer will decide
  what to do with it.

## Setting up

You need macOS, Xcode, and over 100 GB of free disk space. The first build
takes several hours.

1. Install the requirements in [docs/building.md](docs/building.md). That
   page comes from Helium, so it uses Helium's names. Clone rac instead:
   ```sh
   git clone --recurse-submodules https://github.com/notkainoa/rac.git
   ```
2. Set up the dev environment and build:
   ```sh
   source dev.sh
   he setup
   he build
   he run
   ```

## Making a change

rac changes Chromium through patches, not by editing source in git directly.
[docs/internals/overview.md](docs/internals/overview.md) explains how the
layers fit together and walks through making a patch with quilt.

The rules that matter most:

- **Put rac changes in `patches/rac/`,** listed at the end of
  `patches/series`. Never edit `helium-chromium/` or Helium's own patches.
- **Prefer new files over edits to existing Chromium files.** Keep hooks
  into Chromium small. Every edit to an upstream file is a potential
  conflict when Chromium updates.
- **Keep it fast.** A feature that's turned off should cost nothing.
- **Cover every surface.** The checklist in
  [AGENTS.md](AGENTS.md#cover-every-surface) applies to people too.

## Pull requests

**Every PR must be fully tested, whether written by hand or with AI.**

- **One problem per PR.** If you're fixing two unrelated things, open two
  PRs.
- **Build it and run it.** Exercise the changed behavior in a real rac
  build. Say what you checked and what you couldn't check.
- **Show it.** UI changes need before and after screenshots. Changes
  involving motion, timing, or interaction need a short video. Attach these
  to the PR; don't commit them to the repo.
- **Explain it.** Describe the problem, then how your change fixes it.
- **Commit titles** use conventional commits, such as
  `feat(spaces): add space switcher dots` or
  `fix(sidebar): stop flicker on reveal`.
- **Run `he validate series`** if you changed `patches/series`.

## Using AI

AI-assisted contributions are welcome. The same rules apply as for any PR:
you must understand the change, test it yourself, and include the evidence.
At the end of the PR description, say which model and tool you used. If your
agent reads repo instructions, point it at [AGENTS.md](AGENTS.md).

## License

rac is licensed under GPL-3.0. By contributing, you agree that your
contribution is released under the same license. If you include code from
another project, make sure its license is compatible and credit it in the
PR.
