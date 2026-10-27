# Thread brief: Power (power features)

> **DRAFT: do not launch until the maintainer approves the plans.**

Follow ["Every thread"](README.md#every-thread) in the README: reading, step 0, streams, the build queue, moving to 156, workflow stages, verification standard, and hard constraints. This brief adds only what is specific to Power.

## Goal

Add what Arc refugees reach for daily: clean links, Copy as Markdown, group naming, Boosts, Air Traffic Control (link routing), and bangs, with no second action table and no network calls. Start on day 1 with pure logic. Hooks follow once Core's table lands, about day 16, and the first ship in the first point release, about day 26.

## Owns

Plan 07 M0 to M5. Before launch, only pure logic with unit tests: `rac::SitePattern`, the clean-link strip table, and the naming rule.

## Decisions it depends on

- **Group A:** D9a/b/c, D63.
- **Needed before hooks, about day 16:** D48 (order), D31 (shortcuts; taking Opt+Cmd+N needs the maintainer's OK).
- **By milestone:** D49 and D50 (07 M1, day 16), D54 (Boosts, before M2's build, day 20; VISION wording), D51 (M3, day 24), D52 (M5 go or no-go, about day 35), D53 (themes vs space colors), D12a/b, D17.

## Plan-specific reading

`plans/07-power-features.md`, `docs/internals/bangs.md`, plan 03 M1 (action table), plan 01 M3 (router). Credit Ardia and Stedding with their notices.

## Streams

| Stream | Branch | Days | Work |
| --- | --- | --- | --- |
| `logic` | `feat/power-logic` | 1-6 | `rac::SitePattern`, `rac::CleanLink()`'s strip table, and Ardia's naming rule, with unit tests only. No hooks |
| `logic`, then per milestone | `feat/power-<m>` | 10 on | Boosts spike (days 10-14, if a run slot is free). After Core's table lands: M0 fields (days 16-20), M1 hooks (days 16-24), M4 bangs editor (days 16-26). M3 after UI's router (day 24 on). M2's build from day 20 |

Before launch, Power has one stream. It adds streams after launch, one per milestone, when their files don't collide.

## Machine and worktree

- The Air, through the queue, at normal priority. Before launch, only unit-test builds, in a light worktree that runs `setup` when its first batch is ready.
- Hooks are written only on the 156 base, after Core's table merges.
- Air Traffic Control tests send links through UI's `open-urls` harness verb. No step changes the default browser; the maintainer checks the real default-browser flow by hand on a second macOS user.
- Never touch real profiles or real agent configs.

## Power adds to the verification standard

Unit tests for `SitePattern`, the strip table (including cases that must not change), and Ardia's naming cases ported one for one; shots in two spaces and incognito where it applies; motion videos with Reduce Motion on and off; a net log showing no requests; zero Boosts means no script and no file read at startup.

## Coordination

- No second action table: add fields and rows to Core's table (03 M1). Use the schema Core publishes on day 1.
- M3 waits for UI's router (01 M3). M5 needs its own go-ahead after a Helium diff check.
- Shared files: `browser_shortcut_metadata.cc`, `spaces/commands.patch`, `browser_commands.cc`, the site control center (UI, Core), omnibox and bangs files (UI, Helium). Every per-site entry goes through site controls placed by UI.
- Nothing merges before the sync, and Power's hooks merge only after the launch build fires.
- With AI off, no AI button (the group "Name with AI" button exists only with AI on).

## First steps

Day 1:

1. Write `rac::SitePattern` in `chrome/browser/rac/site_pattern/`: host and subdomain matching, "URL contains", case-insensitive, using Chromium's registrable-domain helper.
2. Write `rac::CleanLink()`'s strip table, based on Stedding's L2 table (BSD-3, notice kept), with cases that must not change.
3. Port Ardia's 99-line naming rule (Apache-2.0, credited) and its cases.
4. Unit tests for all three. Build them once, as one batch, through the queue.

Then, once Core's table lands: add "default shortcut" and "menu label" fields, and make Helium's shortcut metadata read them through one hook, replacing the per-command hunks in `spaces/commands.patch`. This rewrites merged work: re-test every space shortcut. Expect about 2 hunks replacing 4.

## Done means

Each milestone's acceptance in plan 07 passes: for example `https://x.com/a?utm_source=y&id=3#c` copies as `https://x.com/a?id=3#c`, three GitHub PR tabs name a group "GitHub", and Boosts apply before first paint, survive restart, and work in incognito. Each PR has proof and its hunk delta.
