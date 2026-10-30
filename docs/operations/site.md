# The website

rac's marketing site lives in `site/`: a static [Astro](https://astro.build)
site with Tailwind and three React islands (the browser window, the space
editor, and the assistant), animated with Motion. It has no analytics, cookies, third-party scripts, or fonts
from other servers, because "nothing phones home" applies to the site too.

## Layout

The repo is a light pnpm workspace. The browser build stays exactly where it
was at the root (`patches/`, `resources/`, `dev.sh`, `build.sh`, the
`helium-chromium/` submodule, `.github/`), because Chromium builds, quilt,
and feature worktrees depend on those paths. The root `package.json` and
`pnpm-workspace.yaml` only add `site/` as the `@rac/site` package, and none
of the browser tooling reads them.

## Run and build

From the repo root, with Node 22.23.4 or later and the pnpm version pinned in
`package.json` (`corepack enable` picks it up):

```sh
pnpm install
pnpm site:dev       # dev server with hot reload
pnpm site:build     # static build into site/dist/
pnpm site:preview   # serve the build locally
```

None of these need a Chromium build or `he`.

## Things to know before changing it

- **`RELEASE_READY`** in `site/src/config.ts` decides how the site treats
  downloads. While it's `false`, the download buttons say "Coming soon, star
  the repo" and link to the repository, and `/download` is hidden: no
  link points to it, search engines skip it, and it shows sample data. Set
  it to `true` with the first release (see
  [Releases](releases.md#the-website)).
- **The download page** is Apple silicon only. It shows one "Download for
  Mac" button, labelled "Apple silicon (M1 or later), macOS 13 Ventura or
  later". On a Mac it knows has Apple silicon, it starts the download once
  per visit. On an Intel Mac it says rac needs Apple silicon and downloads
  nothing. When the browser won't say which chip (Safari often won't), it
  doesn't auto-download. Versions before 0.2.0 are labelled "Preview. Not
  for daily use." It reads the latest GitHub release when the site builds
  (`site/src/lib/release.ts`) and uses only the `_arm64-macos.dmg` asset,
  so visitors never contact GitHub's API. If the release has no arm64 disk
  image, or GitHub doesn't answer, the build fails and the last good
  deployment stays live.
- **The windows are working drawings of rac.** `site/src/components/rac/`
  rebuilds the sidebar, space editor, and assistant panel in HTML. Sizes were
  measured from the running browser. Colors and the eight space themes are
  copied from rac's patches in `patches/rac/` (`rac_color_mixer.cc`,
  `space.cc`, `space_tint_background.cc`, and
  `chrome/browser/resources/rac_ai/app.css`), and the assistant's card
  wording is rac's own. When one of those changes in rac, update `theme.ts`
  or `rac-ui.css` so the site keeps telling the truth.
- **Link previews** use `site/public/og.png`, a 1200×630 capture of the
  home page's headline and window. Retake it when the hero changes.
- **Ad blockers hide some class names.** rac ships uBlock Origin, and its
  lists hide elements named like ads on every site: `.ad-panel` and
  `.ad-card` once hid the whole assistant demo. Don't start class names
  with `ad-`, `ads-`, `banner`, `promo`, or `sponsor`.
- **Screenshot slots.** Each drawing sits in a `<ProductShot>` whose `name`
  says which real screenshot could replace it later.
- **Keep it private.** Don't add analytics, embeds, or a font service. When
  deploying, leave the host's own analytics and script injection off
  (Vercel Web Analytics and Speed Insights, Cloudflare Web Analytics).

## Deploy

Vercel builds the site from GitHub. The project is `rac` in the
`knewton` team, and production is <https://racbrowser.com>.

- **Pull requests** get a preview deployment, and Vercel comments the link
  on the PR. Previews sit behind Vercel's login.
- **Pushes to `main`** deploy to production.
- **Changes outside the site skip the build.** The project's root directory
  is `site/`, with "skip deployments when there are no changes to the root
  directory or its dependencies" turned on. A patch-only PR gets no
  preview.

The build settings live in `site/vercel.json`. The project also sets
`ENABLE_EXPERIMENTAL_COREPACK=1`, so Vercel uses the pnpm version pinned in
the root `package.json`.

The build is plain static files, so another static host works too: build
`pnpm site:build` from the repo root and serve `site/dist`. The site
doesn't need the `helium-chromium` submodule, so turn off submodule cloning
if the host offers that.
