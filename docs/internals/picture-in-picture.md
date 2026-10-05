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
- **Leaving includes switching apps.** `auto-pip-on-app-switch.patch` opens
  PiP when another regular app (one with a Dock icon) takes focus from rac,
  and closes it when rac is in front again. Menu bar apps and launchers
  (Spotlight, Raycast, 1Password's quick access) don't count, because they
  open briefly over the video. The check lives in `rac::AppFocusObserver` and
  only runs while a tab has a video that could open PiP.
- **Leaving includes hiding the window.** `auto-pip-defaults.patch` turns on
  `kAutoPictureInPictureOnWindowOccluded`, so PiP also opens when macOS
  reports the window as hidden, for example on another desktop or behind a
  full-screen app.
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
  the tab stops being the active tab in its window's `TabStripModel`, or the
  occlusion helper reports the window as occluded (hidden by macOS, or
  another app in front). If switching rac spaces hides tabs some other way,
  auto-PiP won't fire on a space switch.
- **macOS almost never reports a window as covered.** macOS counts a
  window's shadow, so another window has to extend roughly 60 pt past rac on
  every side before rac counts as occluded. Chromium's own frame check is
  off on macOS 26 and only looked at Chromium windows. With Stage Manager,
  other apps never cover rac at all; its window shrinks into the strip and
  stays "visible". App focus is the signal that works, which is why the
  app-switch patch exists.
- **App focus is an approximation.** PiP opens when another app is in front
  even if rac's video is still on screen, such as on a second display or
  grouped in the same Stage Manager stage. Clicking the PiP window doesn't
  bring rac forward (`pip-over-fullscreen-apps.patch` makes it
  non-activating), so it doesn't close PiP.
