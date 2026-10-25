# Proposed roadmap revision (2026-10-22)

> Text extracted from an HTML page rendered in the maintainer's planning thread. Not committed to main before. Treat as context, not as decided.

Phase 4 is now the only phase with a fixed order: icons and DMG art, then onboarding, then the rest in any order. Every other phase runs in parallel worktrees, foundations first.
builtplannedfrom Ardianew in this revisionfoundation land first1 fixed order· any order
0
Working build
done
Unmodified Helium builds from this repo
Docs, agent guide, feature worktrees
1
Make it rac
done
Identity foundation
Name, bundle ID, data dir, keychain. Side by side with Helium.
Cut Helium services
Crash reporting off; the rest stays behind Helium's consent.
Updater
Own version, GitHub feed, own signing key.
Name pass
"Helium" → "rac" in user-facing text.
2
Foundations
built
Spaces foundation
Model, switching, dots, saving, unloading, sliding pages. 26 patches.
Pinned tabs and favorites
Folders, reset, drag, snap. 18 patches.
Sidebar hide and reveal
⌘S, left and top edge reveal, full or hidden only.
Address bar in the sidebar
10 patches, plus the site control center.
Auto picture-in-picture
Any video, app switch, permission, incognito.
3
Finish what's built
nowany order
Everything here exists in patches or is close to it. Clean and fully working, not more scope. Independent of each other; run in parallel.
Space themes built
Color, gradient, icon per space.
AI basics built
Side panel, NTP ask, ⌘F Ask, link summaries. 42 patches.
Agent: finish what exists built also in 5
The 21 patches as they are: snapshot, tools, MCP server for the agent rac launched, guard, critic, confirm cards, indicators. Every path works end to end, the open concerns in internals/ai.md closed, left clean. No new capability; refinement is phase 5.
Settings cleanup built
Appearance, Behavior, General, About.
Media controls in the sidebar
On Chromium's media controls.
Bangs from 4
Settings page to view, edit, add; edits survive list updates; address bar flow. Design first.
Micro-interactions from 4 enriched
One worktree per area. Timings from Ardia's measured Dia spec.
docs/dia-spec.md
4
Ready to release
fixed order, then any
Icons first, onboarding second. The rest in any order, except that the bench should land before the power patches so each one is measured, and the Helium sync before the bench's baseline.
1 Icons and DMG art
App icon, logos, DMG background, in resources/ only. No build needed; can start today.
2 Onboarding
First run: AI opt-in, space theme, sidebar layout, Helium's importer for now (the full importer is phase 5).
Then, any order
· Sync to Helium 0.19 / Chromium 155
From 0.18.2.1. Before the bench baseline. Full rebuild; needs your OK.
· Perf bench vs Helium + ratchet from Ardia
Launch, idle CPU, memory at 20 tabs, tab switch, new tab, typing. Interleaved with Helium. Ceilings only go down.
· Sign, notarize, nightly channel from Ardia
One appcast, nightly channel, GitHub prerelease, channel picker in About.
· CI and stable releases
Replace Helium's workflows, DMG, deltas, the perf gate.
· Power and frame patches → rac/perf/ from Ardia
After the bench. 120 Hz after tab switch, full rate while scrolling, frozen tabs keep WebSockets, begin-frame warm-up, Battery Saver lifts for input. Credited.
· Crash reports from Later
Off by default, per-crash yes. rac's only server.
5
After the release
any order
Agent: refine and open up also in 3
Other agents on this Mac control rac over its MCP server, not only the one rac launched. Permissions: what an outside agent may touch, per agent, revocable. Design this before the rest of the agent work. Look and feel of confirm cards, indicators, panel, motion.
Import from every browser from Ardia
Detects what's installed and what used to be, from profile folders still on disk. Chrome, Safari, Firefox, Edge, Brave, Opera, Vivaldi, Island, Chromium, Arc, Dia. Arc's spaces become real spaces. Absorbs Arc import and Dia import.
Command bar enriched
Tabs, history, actions, AI. Sums, doc.new shortcuts, tab-to-search, inline completion.
Air Traffic Control from Later
Route links to the right space by site. Shares a site-to-space model with import.
Clean links on copy
Tracking parameters stripped on copy and share.
Tab clean-up
Untouched tabs sweep into Recently Cleaned, recoverable.
Auto-named tab groups
From titles when AI is off; by the model when on.
Little Arc
Small window for links from other apps.
Boosts
Custom CSS and JS per site, with an editor.
6
One at a time
not a real phase
Hand-off to agents on other devices
Phase 5 covers agents on this Mac; this hands a task to an agent elsewhere with its own machine: a Grok bot, Muse, and the like. rac packages the context (page, task, approvals), hands it over, shows where the work went and what came back. Replaces cloud agents and outside-MCP rows.
Video upscaling
Apple super resolution on video layers. 21 files in viz and the GPU process.
On-device translation
macOS 26 Translation framework.
Safe automation endpoint
Token-gated CDP server for our harness and agent.
Host Helium's services
Automations
On a schedule or trigger.
1Password and wallet
Sync
Ardia's iCloud E2E design is the reference.
?
Not planned
no phase
Notes and easels
Possible one day.
iOS · Linux · Windows
Wanted. Far out.
Not taking from Ardia: telemetry, kill switches, counted update checks, website session replays, Google suggestions on by default, component-updater restriction (Helium covers it), live folders, React Native anything.
