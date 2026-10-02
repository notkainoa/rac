# Roadmap

The order in which rac gets built. Phases are roughly sequential, but small
items can land early. This page lists what each phase covers. Track active
work in GitHub issues, not here.

Status: **phase 0**. rac builds as stock Helium.

## Phase 0: Working build

- Build and run unmodified Helium from this repo on the maintainer's Mac.
- Project docs, contribution guide, and agent guide (this page and its
  neighbors).

## Phase 1: Make it rac

Nothing gets shared with other people until this phase is done.

- **Cut ties to Helium's servers:** turn off or replace update checks, crash
  reporting, and Helium services. See
  [internals/overview.md](internals/overview.md#branding-and-helium-services).
- **Updates:** rac's own Sparkle feed and signing key, or updates turned
  off until there is one.
- **Signing:** the maintainer's own Apple Developer ID and team ID, and
  notarization.
- **Branding:** app name, bundle ID, keychain name, data directory, icons,
  DMG, and `rac://` internal pages. rac and Helium must be installable side
  by side.
- **Name pass:** a substitution step after Helium's that turns "Helium" into
  "rac" in user-facing text.
- **Onboarding:** rac's own first-run flow.
- **GitHub:** adapt or remove Helium's CI workflows (especially `bump.yml`),
  and turn on Issues and private vulnerability reporting.

## Phase 2: Sidebar and spaces

- Spaces inside each profile window, each with its own color theme and icon.
- The space switcher dots at the bottom of the sidebar.
- Favorites shared across a profile's spaces (Helium's "pinned").
- Arc-style pinned tabs for each space.
- Cmd+S fully hides and shows the sidebar by default. A setting switches it
  back to compact mode (Helium's current behavior).
- An appearance setting that moves the address bar into the sidebar.

## Phase 3: Polish

- Polished edge reveal for the hidden sidebar and toolbar.
- Gradient space themes.
- Micro-interactions across the interface.
- Media controls in the sidebar.
- Automatic picture-in-picture when leaving a tab with a playing video.

## Phase 4: Command bar and boosts

- The command bar, available in place of the new tab page.
- Boosts: custom CSS and JavaScript for each site.

## Phase 5: AI basics (to be designed)

Designed from scratch when this phase starts. See
[internals/ai.md](internals/ai.md) for the ideas so far.

- The onboarding opt-in and settings toggle.
- Providers.
- The AI sidebar that reads the current page.
- AI in the new tab page, Cmd+F, and link hover.

## Phase 6: Agent (to be designed)

- Browser control across tabs, with user confirmation.
- A safety check on agent actions.

## Later

No order and no promises:

- Automations on a schedule or trigger
- 1Password integration and a wallet
- Letting outside agents use rac's browser tools through MCP
- Cloud agents (exploring)
- Air Traffic Control (routing links to the right space)
- Little Arc (a mini window for links opened from other apps)
- Notes and easels
- Sync
- iOS app
- Linux and Windows
