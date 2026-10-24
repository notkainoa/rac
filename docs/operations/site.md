# The website

rac's marketing site lives in `site/`: a static [Astro](https://astro.build)
site with Tailwind and one React island (the hero's browser window, animated
with Motion). It has no analytics, cookies, third-party scripts, or fonts
from other servers, because "nothing phones home" applies to the site too.

## Layout

The repo is a light pnpm workspace. The browser build stays exactly where it
was at the root (`patches/`, `resources/`, `dev.sh`, `build.sh`, the
`helium-chromium/` submodule, `.github/`), because Chromium builds, quilt,
and feature worktrees depend on those paths. The root `package.json` and
`pnpm-workspace.yaml` only add `site/` as the `@rac/site` package, and none
of the browser tooling reads them.

## Run and build

From the repo root, with Node 22 or later and the pnpm version pinned in
`package.json` (`corepack enable` picks it up):

```sh
pnpm install
pnpm site:dev       # dev server with hot reload
pnpm site:build     # static build into site/dist/
pnpm site:preview   # serve the build locally
```

None of these need a Chromium build or `he`.

## Things to know before changing it

- **The download button** reads `RELEASE_READY` in `site/src/config.ts`.
  While it's `false`, every button says "Coming soon, star the repo" and
  links to the repository. Set it to `true` when the first release is on
  GitHub, and the buttons link to the latest release.
- **Product pictures are drawings.** The browser windows and sidebars are
  built in code from the real layout, inside `<ProductShot>` slots. Each
  slot has a `name` saying which screenshot belongs there once rac's UI
  settles.
- **Generated assets.** `site/scripts/make-horizon.mjs` draws the dithered
  horizon behind the hero. `site/scripts/make-display-font.py` makes the
  trimmed Newsreader file the headlines use. Rerun them rather than editing
  their output by hand.
- **Keep it private.** Don't add analytics, embeds, or a font service. When
  deploying, leave the host's own analytics and script injection off
  (Vercel Web Analytics and Speed Insights, Cloudflare Web Analytics).

## Deploy

The build is plain static files, so any static host works. Both of these
build from the repo root:

| Host | Build command | Output directory |
| --- | --- | --- |
| Cloudflare Pages | `pnpm site:build` | `site/dist` |
| Vercel (framework preset: Other) | `pnpm site:build` | `site/dist` |

The site doesn't need the `helium-chromium` submodule, so turn off
submodule cloning in the host's settings if it offers that.
