# Roadmap

The order in which rac gets built. This page lists what each phase covers.
Track active work in GitHub issues, not here.

Status: **phase 1**. rac builds and runs, but it's still stock Helium.

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
| Cut Helium services | Crash reporting off; decide what replaces extension downloads, uBlock lists, and anything sync uses on Helium's servers | Service prefs and URLs |
| Updater | Sparkle off until rac has releases, then rac's own feed and signing key | `macos/updater/` |
| Icons and DMG art | App icon, logos, DMG background | `resources/` only |
| Name pass | A substitution step after Helium's that turns "Helium" into "rac" in user-facing text | New substitution step |
| Onboarding | rac's own first-run flow, using Helium's existing Arc importer | Onboarding page |
| CI and releases | Replace Helium's workflows (especially `bump.yml`), signing, notarization, packaging | `.github/`, signing scripts |

Helium's servers and branding are listed in
[internals/overview.md](internals/overview.md#branding-and-helium-services).
When Identity renames `Helium.app`, update `he run` and
`devutils/rac/worktree.sh run` to match.

Decisions needed before this phase can finish:

- The bundle ID. It's hard to change after people install rac.
- Whether to keep using Helium's services for extension downloads and
  uBlock lists, go direct, or host rac's own.
- Whether updates stay off until there are public releases.
- An Apple Developer account for signing and notarization, needed before
  sharing builds.

## Phase 2: Foundations

Large, independent pieces in separate areas of the code. All of them can
be built in parallel. Spaces is the foundation for phase 3; build it as an
ordered chain in one worktree (data model, switching, dots, saving).

| Feature | Covers | Code it touches |
| --- | --- | --- |
| **Spaces** | Spaces inside each profile window, each with its own tabs; the switcher dots at the bottom of the sidebar; saved across restarts | Tab model, vertical sidebar |
| Sidebar hide and reveal | Cmd+S fully hides and shows the sidebar by default, a setting switches back to compact mode (Helium's behavior), and polished edge reveal for the hidden sidebar and toolbar | Helium's layout (compact and zen mode) |
| Command bar | A quick launcher for tabs, history, and actions, available in place of the new tab page | New rac page, new tab page hook |
| Boosts | Custom CSS and JavaScript for each site, with an editor | Content script injection, new rac page |
| Auto picture-in-picture | Video pops out when you leave a tab where it's playing | Media and picture-in-picture |

## Phase 3: Built on spaces

Needs Spaces from phase 2. Pinned tabs and favorites both change the tab
list, so expect small conflicts between them. Merge whichever finishes
first, then sync the other.

| Feature | Covers | Code it touches |
| --- | --- | --- |
| Space themes | A color, gradient, and icon for each space | Themes and colors |
| Pinned tabs | Arc-style pinned tabs that stay in one space's sidebar | Tab list |
| Favorites | Helium's pinned tabs as icons at the top of the sidebar, shared by every space in a profile | Top of the tab list |
| Address bar in the sidebar | An appearance setting that moves the address bar into the sidebar | Sidebar header, location bar |
| Media controls in the sidebar | Built on Chromium's media controls | Bottom of the sidebar |

## Phase 4: Polish

| Feature | Covers |
| --- | --- |
| Arc import | Bring Arc's spaces, pinned tabs, and favorites into rac's |
| Onboarding update | Space themes, import, and sidebar layout choices in the first run |
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
