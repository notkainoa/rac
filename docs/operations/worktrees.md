# Feature worktrees

Each feature can live in its own git worktree with its own Chromium build
tree. You can work on several features at once and test each one separately.

A full build tree is over 100 GB and takes hours to build. A worktree doesn't
copy it. It gets an APFS copy-on-write clone of the main checkout's built
tree, which takes about 30 seconds and almost no disk space until files
change. The first build in a new worktree takes a minute or two. After that,
builds only redo what the feature's patches change.

## The main checkout is the base

Every new worktree clones `build/src` from the main checkout. Keep that tree
built and matching `main`, and do feature work in worktrees instead.

Setup refuses to clone while a build is running in the main checkout.

## Creating a worktree

In the Factory App, create a new worktree and pick the **rac feature tree**
setup profile. It comes from `.factory/worktree-setups/rac.yaml`.

Without Factory:

```sh
git worktree add -b feat/<name> <path> main
cd <path>
devutils/rac/worktree.sh setup
```

Setup checks out the Helium submodule from the main checkout, merges the
patches, clones the build tree, points it at the new worktree, and applies
any patches that differ from the main checkout's. Like every `sync`, it also
applies rac's names to the dev tree (see
[Branding](../internals/overview.md#branding-and-helium-services)).

## Working in a worktree

- Build with `source dev.sh && he build`, the same as in the main checkout.
- Run with `devutils/rac/worktree.sh run`, not `he run`. `he run` uses
  one shared dev profile. If two builds launch with the same profile, the
  second one only opens a window in the browser that's already running.
  `run` gives each worktree its own profile in `build/profile`.
- Make patches with the quilt workflow in
  [overview.md](../internals/overview.md#making-a-rac-change). Commit after
  `he unmerge`, then run `he merge` to keep working.
- Before a rebase or `git pull`, save quilt edits with `quilt refresh`, then
  run `he unmerge`. Afterward, run `he merge`,
  `devutils/rac/worktree.sh sync`, then `he build`.

Run `sync` by itself. Until it finishes, don't edit `build/src` or `patches`,
run Quilt or Git operations, or start another sync in that worktree. Use
separate feature worktrees for parallel work. Preflight protects existing
edits; it cannot protect writes made concurrently with restoration.

If a build in a worktree shows tens of thousands of steps, something
invalidated the clone. Stop it and find out why before letting it run for
hours.

## Updating the base

After merging features into `main`, update the main checkout so new
worktrees start from it. First save any quilt edits with `quilt refresh`.
Unmerge before pulling or rebasing: doing it afterward can overwrite the
incoming `patches/series`.

```sh
he unmerge
git pull
he merge
devutils/rac/worktree.sh sync
he build
```

`sync` pops only the patches that changed, plus every patch applied after
them, and then applies the new versions. A change to a late rac patch
rebuilds a few files. A change to an early Helium patch can rebuild most of
Chromium.

Existing worktrees don't follow the base on their own. To bring one up to
date, save quilt edits with `quilt refresh`, run `he unmerge`, rebase its
branch onto `main`, run `he merge`, then `devutils/rac/worktree.sh sync` and
`he build`.

## Removing a worktree

Cleanup (`devutils/rac/worktree.sh cleanup`, run by the Factory profile)
stops any build or browser running from the worktree. It then moves
`build/` into the main checkout's `build/.trash/` and deletes it in the
background. Setup and cleanup also clear trees left there by an interrupted
delete.

Git refuses `git worktree remove` without `--force` because the worktree
contains the Helium submodule. Factory won't remove these worktrees
automatically either, because the merged patches count as untracked files.
Delete them yourself when the feature is done.

## How the clone is made usable

A cloned tree still refers to the main checkout in three places. Setup fixes
each one:

- **Siso's file state** (`out/Default/.siso_fs_state`) is keyed by absolute
  path. Without it, siso treats every step as dirty and rebuilds all of
  Chromium. Setup exports the state with `siso fs export`, rewrites the
  paths, and imports it back.
- **GN's build files** contain absolute paths for a few rules, such as
  Helium's onboarding page and uBlock. Setup reruns `gn gen`. Those rules
  then rerun once, which explains most of the 46 steps in the first build.
- **Quilt** records the patches folder in `.pc/.quilt_patches`. Setup points
  it at the worktree's `patches/`.

`sync` records each applied patch's hash in `build/src/.pc/.rac_applied` and
keeps its original bytes in `.pc/.rac_patch_bytes/`. Before popping patches,
it reconstructs their saved changes and checks affected source files,
including edits outside the top patch. Unsaved edits or unverifiable old
records stop sync before it changes files or restores names.

When the stack matches and both name passes are already applied, `sync`
skips restoration, archive validation, and rewriting patch records. It
still updates the generated rac version fields.

Keep those records and the `.rac_names/` backups. Deleting them to bypass a
refusal can lose edits. For an unbranded tree whose applied patches are
already saved, the checked initializer can verify and recreate the record:

```sh
python3 devutils/rac/worktree_state.py record build/src patches
```

It refuses if it cannot verify the supplied patch versions against the
sources. Restoring old name backups without expected fingerprints also
refuses; preserve them and any string edits rather than adopting the
current files as a clean baseline.
