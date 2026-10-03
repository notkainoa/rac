# rac docs

Start with the [vision](../VISION.md) to learn what rac is and isn't, then the
[roadmap](roadmap.md) for what's being built and in what order.

## Working on rac

- [Contributing](../CONTRIBUTING.md): how to propose and submit changes
- [Building](building.md): requirements, release builds, and the `he` dev
  tool. This file comes from Helium, so it says "Helium" and `helium-macos`.
  For rac, use this repo instead.

## Internals

These pages record how rac is put together, decisions and the reasons behind
them, and traps that are hard to spot from the source.

- [Overview](internals/overview.md): the layers, repo layout, how patches
  are applied, and how to make a rac change
- [Glossary](internals/glossary.md): the words rac uses for things
- [AI (work in progress)](internals/ai.md): ideas collected so far; nothing
  decided

## Operations

- [Syncing with Helium](operations/upstream-sync.md): pulling in new Helium
  and Chromium releases
- [Feature worktrees](operations/worktrees.md): working on several features
  at once, each with its own build tree
