# Roadmap

The order in which rac gets built. This page lists what each phase covers.
Track active work in GitHub issues, not here.

Status: **phase 2**. rac has its own name, bundle ID, data directory,
version, and updater, with Helium's icons and services. Phase 1's icons,
DMG art, onboarding, and release setup are put off until later; they're
still needed before sharing builds.

## How the phases work

Phases follow dependencies. The features in a phase touch different parts of
the code, so they can be built at the same time in separate
[feature worktrees](operations/worktrees.md) without their patches
colliding.

- **Land the foundation first.** Some phases start with a foundation that
  the rest of the phase builds on. Merge it, update the base build, then
  start the other worktrees from the new base.
- **Keep 3–5 worktrees going at once.** The limit is how many features the
  maintainer can review and test, not disk space or CPU.
- **Design work can happen any time.** Icons, theme designs, and the AI
  design need no build, so they can run ahead of their phase.
- **Small items can land early** when they don't touch another phase's
  code.

## Phase 0: Working build (done)

- Build and run unmodified Helium from this repo on the maintainer's Mac.
- Project docs, contribution guide, agent guide, and feature worktrees.

## Phase 1: Make it rac

Nothing gets shared with other people until this phase is done.

Foundation: **Identity.** It causes a large rebuild, so merge it before
branching the rest.

| Feature | Covers | Code it touches |
| --- | --- | --- |
| **Identity** (first) | App name, bundle ID, data directory, keychain name, Apple team ID. rac and Helium must be installable side by side. | Branding, product directory, keychain |
| Cut Helium services | Crash reporting off; Helium's other services stay | Service prefs and URLs |
| Updater | rac's own version, feed on GitHub releases, and signing key, independent of Helium services | `rac/updates/`, release scripts |
| Icons and DMG art | App icon, logos, DMG background | `resources/` only |
| Name pass | A substitution step after Helium's that turns "Helium" into "rac" in user-facing text | New substitution step |
| Onboarding | rac's own first-run flow, using Helium's existing Arc importer | Onboarding page |
| CI and releases | Replace Helium's workflows (especially `bump.yml`), signing, notarization, packaging | `.github/`, signing scripts |

What's done and what still talks to Helium is in
[internals/overview.md](internals/overview.md#branding-and-helium-services).

Decided:

- The bundle ID is `me.kainoa.rac`.
- rac has its own version number and checks only its own GitHub releases
  for updates, with its own setting on the About rac page.
- Helium's services (extensions, bangs, spell check, uBlock lists,
  component updates) stay as they are, labeled as Helium's and behind its
  consent screen. rac may host its own copy later.
- Helium's icon stays until rac's is designed.

Still needed before sharing builds:

- An Apple Developer account for signing and notarization.
- The update signing key in GitHub secrets (see
  [Releases](operations/releases.md#one-time-setup)).

## Phase 2: Foundations

Spaces is the foundation; build it as an ordered chain in one worktree (data
model, switching, dots, saving). Sidebar hide and reveal, the address bar in
the sidebar, and auto picture-in-picture are independent and can start right
away. Pinned tabs and favorites need the spaces data model, so start them
once that part of Spaces is merged.

| Feature | Covers | Code it touches |
| --- | --- | --- |
| **Spaces** | Spaces inside each profile window, each with its own tabs; the switcher dots at the bottom of the sidebar; saved across restarts | Tab model, vertical sidebar |
| Pinned tabs and favorites | Arc-style pinned tabs that stay in one space's sidebar, loose or in folders, each remembering the page it was pinned on with a way to reset back to it; and favorites (Helium's pinned tabs) as icons at the top of the sidebar, shared by every space in a profile. One feature, because both reshape the top of the tab list | Tab list |
| Sidebar hide and reveal | Cmd+S and the sidebar button fully hide and show the sidebar by default, and a setting switches back to compact mode (Helium's behavior). In both hidden and compact, moving the mouse to the left edge shows the full sidebar over the page. Polished edge reveal for the hidden toolbar too | Helium's layout (compact and zen mode) |
| Address bar in the sidebar | An appearance setting that moves the address bar into the sidebar | Sidebar header, location bar |
| Auto picture-in-picture | Video pops out when you leave a tab where it's playing | Media and picture-in-picture |

Unmerged Helium pull requests worth reading first. They're ideas to learn
from, not code to copy as-is; none were merged, and some were closed for
being too large.

- Pinned tabs: [helium#1578](https://github.com/imputnet/helium/pull/1578)
  ("anchored tabs"). Its per-tab behavior is what rac wants. rac's section
  differs: it holds loose tabs as well as folders.
- Sidebar hide and reveal:
  [helium#1035](https://github.com/imputnet/helium/pull/1035) (expand the
  compact sidebar on hover). Chromium also has its own expand-on-hover for
  vertical tabs, behind a disabled feature flag.
- Address bar in the sidebar:
  [helium#2367](https://github.com/imputnet/helium/pull/2367). The look is
  right; the approach needs a fresh review.
- Auto picture-in-picture:
  [helium#1765](https://github.com/imputnet/helium/pull/1765). Chromium has
  related flags, such as `auto-picture-in-picture-on-window-occluded`.

## Phase 3: Themes and tools

Space themes needs Spaces from phase 2. The rest are independent of each
other and can be built in parallel.

| Feature | Covers | Code it touches |
| --- | --- | --- |
| Space themes | A color, gradient, and icon for each space | Themes and colors |
| Command bar | A quick launcher for tabs, history, and actions, available in place of the new tab page | New rac page, new tab page hook |
| Boosts | Custom CSS and JavaScript for each site, with an editor | Content script injection, new rac page |
| Media controls in the sidebar | Built on Chromium's media controls | Bottom of the sidebar |

## Phase 4: Polish

| Feature | Covers |
| --- | --- |
| Arc import | Bring Arc's spaces, pinned tabs, and favorites into rac's |
| Onboarding update | Space themes, import, and sidebar layout choices in the first run |
| Bangs | A settings page to view, edit, delete, and add bangs, with edits that survive list updates, and a rethought address bar experience for bangs. Design first; see [internals/bangs.md](internals/bangs.md) |
| Performance check | Startup, tab switching, scrolling, and typing compared with Helium, with each feature on and off |
| Micro-interactions | Tasteful motion, one worktree per area (sidebar, spaces, command bar) |

## Phase 5: AI basics (to be designed)

Designed from scratch, in a design doc that can be written during an
earlier phase. See [internals/ai.md](internals/ai.md) for the ideas so far.

Foundation: **AI settings.** The onboarding opt-in, the settings toggle, and
providers. When those are merged, these can be built in parallel:

- The AI sidebar that reads the current page.
- AI in the new tab page and the command bar.
- Cmd+F "Ask".
- Link hover summaries.

## Phase 6: Agent (to be designed)

Foundation: **browser control** across tabs, with user confirmation. After
it, the safety check on agent actions can be built in parallel with agent
features.

## Later

No order and no promises:

- rac's own crash reports, off by default and sent only when the user says
  yes after each crash (see [internals/overview.md](internals/overview.md#crash-reports))
- Hosting rac's own copy of Helium's services
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
