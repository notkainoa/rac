# rac

rac is a private, fast, and beautiful macOS browser. It's a fork of
[helium-macos](https://github.com/imputnet/helium-macos), which packages the
[Helium](https://github.com/imputnet/helium) browser, with Arc-inspired
features and design on top. Optional AI is planned but not designed yet.

All of rac's changes live in its own patches, applied after Helium's. That's
what lets rac keep up with every Helium and Chromium release.

Read [VISION.md](VISION.md) before changing anything a user will see. It says
what rac is, what it never compromises on, and what it deliberately won't do.

## What rac never compromises on

The full reasoning is in the vision. In short:

1. **Private.** No data collection, no rac accounts, no ads, nothing that
   phones home to rac.
2. **Never slower than Helium.** A feature that's turned off does no work.
   Watch startup, tab switching, scrolling, and typing for regressions.
3. **Beautiful and calm.** Arc's personality with Dia's simplicity. Tasteful
   micro-interactions; no animation for its own sake, and nothing that
   repaints continuously.
4. **Opinionated.** Good defaults over settings. Add a setting only when
   people genuinely need different behavior.
5. **Cheap to update.** Every edit to an upstream file is a future merge
   conflict. Prefer new files and small hooks.

Treat these as strong defaults. If a rule here conflicts with the task, say
so clearly and get the maintainer's sign-off before breaking it.

## Words

- **You**: the agent reading this file.
- **The maintainer**: the person who runs rac. Usually who you're talking
  to.
- **User**: someone using rac as their browser.

For browser concepts (profile, space, favorites, pinned tabs, sidebar states,
command bar, boost), use the terms in
[docs/internals/glossary.md](docs/internals/glossary.md). In particular,
Helium's "pinned" items are rac's **favorites**. rac's **pinned tabs** are a
separate Arc-style feature.

## Ways to hurt yourself

1. **Sending anything upstream.** Never push to, open PRs against, or file
   issues on any `imputnet` or `ungoogled-software` repository. Helium bans
   contributors for AI-written submissions. The `upstream` remote is
   fetch-only (its push URL is `no_push`); keep it that way.
2. **Editing Helium's code.** Never edit files in `helium-chromium/` (the
   Helium core submodule). Never edit Helium's patches in `patches/helium/`,
   `patches/rebel/`, or `patches/ungoogled-chromium/`. Change their behavior
   with a rac patch that applies afterward. The submodule's
   `AGENTS.md`/`CLAUDE.md` describe Helium's own policy for their repo and
   don't apply to rac's files.
3. **Touching the maintainer's real browser data.** rac is the maintainer's
   daily driver. Never point a build at a real profile folder in
   `~/Library/Application Support/`, such as `net.imput.helium` or rac's own
   once it exists. In the main checkout, use `he run`, which launches with a
   separate dev folder (`net.imput.helium.dev`). In a feature worktree, use
   `devutils/rac/worktree.sh run`, which gives the worktree its own profile.
4. **Destroying the build tree.** `build/src` is a full Chromium checkout,
   roughly 100 GB that takes hours to recreate. Don't run `he reset`, delete
   `build/`, or start a full build without the maintainer's approval. The
   main checkout's tree is also the base that every feature worktree clones
   (see [Worktrees](#worktrees)). In a worktree, `he build` should take
   minutes. If it shows tens of thousands of steps, stop it and tell the
   maintainer.
5. **Moving the submodule by hand.** Don't use `he pull` or
   `git submodule update --remote`. The Helium core version only changes
   when a helium-macos release is merged. See
   [docs/operations/upstream-sync.md](docs/operations/upstream-sync.md).

## Where changes go

| Change | Location |
| --- | --- |
| Chromium or Helium behavior | `patches/rac/<area>/<name>.patch`, listed at the end of `patches/series` under `# rac` |
| Icons, logos, other assets | rac-owned files in `resources/`, wired in through the resource lists |
| Docs | `VISION.md`, `CONTRIBUTING.md`, `docs/` (see [Documentation](#documentation)) |
| Build or CI | Only when necessary; keep it small and isolated |

How patches are applied, and the quilt workflow for making one, are in
[docs/internals/overview.md](docs/internals/overview.md).

## Worktrees

Features are built in git worktrees, each with its own Chromium build tree.
The full procedure is in
[docs/operations/worktrees.md](docs/operations/worktrees.md). Explain it to
the maintainer when they ask how to work on features in parallel.

- **The main checkout is the base.** New worktrees clone its built
  `build/src`, so don't do feature work there.
- **Creating one.** In the Factory App, create a worktree with the
  **rac feature tree** setup profile. Without Factory, run
  `git worktree add -b feat/<name> <path> main`, then
  `devutils/rac/worktree.sh setup` from the new worktree. Setup takes
  about 30 seconds.
- **Building and running.** Build with `source dev.sh && he build` and run
  with `devutils/rac/worktree.sh run`. Never use `he run` in a worktree.
  It shares one profile with every other build, so the second browser only
  opens a window in the first.
- **Committing.** Run `he unmerge`, commit the patch with its
  `patches/series` change, then run `he merge` to keep working.
- **After a rebase or pull.** Run `devutils/rac/worktree.sh sync`, then
  `he build`.
- **Removing one.** Factory runs the cleanup script when it deletes the
  worktree. Without Factory, run `devutils/rac/worktree.sh cleanup`, then
  `git worktree remove --force <path>`. Only remove a worktree when the
  maintainer asks.

Patch rules:

- One feature per patch group, such as `patches/rac/spaces/`. Split large
  features into small, ordered patches.
- Put feature code in new files, for example under `chrome/browser/ui/rac/`.
  Keep edits to existing Chromium files to small hooks: an include, a
  registration call, a build-file entry.
- When removing code, delete the lines instead of commenting them out or
  wrapping them in `#if 0`. This keeps `quilt refresh` reliable.
- Follow Chromium's style. Run `he format` on the topmost patch.
- Build on what Helium already has (vertical layout, compact mode, split
  view, side panels, zen mode, the keyboard shortcut system) instead of
  replacing it.

## Cover every surface

The most common mistake in a browser UI change is something that works where
you tested it and is broken or missing elsewhere. Before calling UI work
done, go through this list and say which items applied:

- **Ways in.** Sidebar, command bar, menu bar, keyboard shortcut, context
  menu, and settings. If a feature can be reached from one, check whether it
  should be reachable from the others.
- **Sidebar states.** Full, compact, and hidden, plus edge reveal.
- **Windows.** Multiple profile windows, multiple spaces, incognito, and
  split view.
- **Appearance.** Light and dark mode, every space theme, and the address
  bar in the toolbar and in the sidebar.
- **Motion.** Reduced motion turned on. Animations never block input.
- **Way back.** If you added a way in, add the way out. Hide needs show;
  pin needs unpin.
- **AI off.** Once AI exists, the feature must work, and cost nothing, with
  AI turned off.
- **Docs.** Check whether the change makes existing docs wrong.

## Verifying

- Prove the change works with the smallest check that shows it: build and
  run with `he build && he run` (`devutils/rac/worktree.sh run` in a
  worktree), then exercise the changed behavior.
- For UI changes, capture before and after screenshots. For motion, timing,
  or interaction, capture a short video.
- Run `he validate series` after changing `patches/series`.
- Don't run Chromium's full test suites. If a change has focused unit tests,
  run only those.
- Ask before driving the browser with computer-use or automation tools.

## Handing off for testing

When a feature is done, or you want the maintainer to try something, make it
one command away. Build first, so the maintainer only has to run it, and
quit any browser you launched. Then send a message like this:

```md
**Ready to test: <feature>**

Worktree: `<absolute path>` (branch `<branch>`)

    cd <absolute path>
    devutils/rac/worktree.sh run

**What changed:** <what a user will notice, in plain words>

**Try this:**
1. <a concrete step, such as "Press Cmd+S twice">
2. <...>

**You should see:** <the expected result for each step, and what looks
different from rac today>

**Not done yet:** <known gaps, surfaces you couldn't check, rough edges>
```

- Give the exact commands with the real path, ready to paste. If the
  maintainer needs to rebuild, include `source dev.sh && he build` first.
- Write the steps for someone who hasn't read the code. Name the menus,
  shortcuts, and settings to use.
- Cover the surfaces from [Cover every surface](#cover-every-surface) that
  apply, such as sidebar states, dark mode, and multiple windows.
- Each worktree's browser starts with an empty profile in `build/profile`
  that persists between runs. Say so if testing needs setup first, such as
  opening several tabs or creating a second space.
- To compare with rac today, the maintainer can run `he run` in the main
  checkout at the same time.

## Commits and pull requests

- Never open a PR unless the maintainer asks.
- Commit titles use conventional commits with plain language:
  - `feat(spaces): add space switcher dots`
  - `fix(sidebar): stop flicker when revealing hidden sidebar`
  - `docs: explain patch layering`
  - `sync: helium 0.18.2.1`
- PR body: the problem, the change, and how it was verified (with
  screenshots or video for UI). End with the model and tool that did the
  work.
- One problem per PR. If the description needs "also," split it.
- Never commit PR-only screenshots or videos. Upload them to the PR instead.

## Documentation

Most changes don't need a doc update. Agents can read the code.

- `VISION.md` is the product direction. Change it only when the maintainer
  changes the direction.
- `docs/internals/` records decisions and the reasons behind them,
  constraints that span several patches, and traps that are hard to see in
  the source. Before adding a paragraph, ask what someone would get wrong
  without it.
- `docs/operations/` holds procedures such as syncing and releases.
- `docs/roadmap.md` lists phases, not task checklists. Track active work in
  GitHub issues.
- `docs/building.md` belongs to Helium. Don't edit it.
- When a documented decision changes, rewrite or remove the old text instead
  of appending a new account.
- Don't commit plans, research notes, or scratch files.

## Licensing

rac includes Helium's GPL-3.0 code and patches, so rac is GPL-3.0. Keep
`LICENSE`, `LICENSE.ungoogled_chromium`, and upstream credits intact. Before
copying code from another project, check that its license is compatible and
credit it.
