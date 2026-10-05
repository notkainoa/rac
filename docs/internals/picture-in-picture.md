# Automatic picture-in-picture

When you leave a tab with a playing video, the video moves into a
picture-in-picture (PiP) window. When you come back, the PiP window closes and
the video keeps playing in the tab. rac builds this on Chromium's own
auto-PiP code (`chrome/browser/picture_in_picture/`) instead of adding its
own, so `patches/rac/pip/` mostly changes defaults.

## What rac changes

- **Any video site can use it.** Chromium normally only auto-opens PiP for
  sites that register a Media Session `enterpictureinpicture` handler, which
  almost none do. `auto-pip-defaults.patch` marks Chromium's
  `BrowserInitiatedAutomaticPictureInPicture` feature stable, so the browser
  opens PiP for any page with a single playing video.
- **Leaving includes covering the window.** The same patch turns on
  `kAutoPictureInPictureOnWindowOccluded`. PiP also opens when macOS reports
  the window as fully covered, which includes switching to another macOS
  desktop. A partly covered window doesn't count, because the video is still
  visible.
- **Allowed by default.** The "Automatic picture-in-picture" site setting
  defaults to Allow instead of Ask, and the settings page offers Allow and
  Block. Under Ask, Chromium shows a prompt inside the first PiP window and
  only opens PiP on sites with high media engagement. Under Allow it skips
  both.
- **Off in incognito unless turned on.** Because the default is now Allow,
  incognito windows would inherit it. `auto-pip-incognito.patch` keeps
  auto-PiP off there unless the user turns on "Allow in incognito windows" on
  the same settings page (`rac.auto_pip_in_incognito`).
- **Floats over full-screen apps.** `pip-over-fullscreen-apps.patch` makes
  the PiP window non-activating and lets it join existing full-screen Spaces,
  the same way Chromium's floating Glic window does.

## What Chromium still decides

Chromium's rules for when not to auto-open PiP stay as they are. The video has
to be making sound (so muted and background videos stay put), the page needs
exactly one playing video in its main frame, the page must be HTTPS or a local
file, and video calls are excluded. Leaving a tab that is visible in split
view doesn't count. A PiP window the user opened by hand never closes on its
own.

## Traps

- **Spaces must change the active tab.** The tab helper fires on two signals:
  the tab stops being the active tab in its window's `TabStripModel`, or its
  `WebContents` becomes occluded. If switching rac spaces hides tabs some
  other way, auto-PiP won't fire on a space switch.
- **Don't trigger on focus loss.** Helium's unmerged
  [helium#1765](https://github.com/imputnet/helium/pull/1765) opens PiP
  whenever the window loses focus. That fires while the video is still on
  screen, for example when clicking into an app beside rac, and needs
  guesswork about displays to undo. Occlusion is the signal that matches
  "you can't see the video anymore".
- **Stage Manager never covers the window.** With Stage Manager on,
  switching to another app shrinks rac's window into the strip instead of
  covering it. macOS still reports it as visible, so PiP doesn't open. That's
  expected, not a bug. Switching to a full-screen app or another desktop
  still opens PiP.
