# Thread brief: Power (power features)

> **DRAFT: do not launch until the maintainer approves the plans.**

Follow ["Every thread"](README.md#every-thread) in the README: reading, step 0, workflow stages, verification standard, and hard constraints. This brief adds only what is specific to Power.

## Goal

After launch, add what Arc refugees reach for daily: clean links, Copy as Markdown, group naming, Boosts, Air Traffic Control (link routing), and bangs, with no second action table and no network calls.

## Owns

Plan 07 M0 to M5. Before launch, only 07 M1's pure logic (the strip table, the naming rule) may be written, with unit tests and no build slot.

## Decisions it depends on

- **Group A:** D9a/b/c.
- **Needed before it starts:** D48 (order), D31 (shortcuts; taking Opt+Cmd+N needs the maintainer's OK).
- **By milestone:** D49 and D50 (M1), D54 (Boosts, before M2; VISION wording), D51 (M3), D52 (M5 go or no-go), D53 (themes vs space colors), D12a/b, D17.

## Plan-specific reading

`plans/07-power-features.md`, `docs/internals/bangs.md`, plan 03 M1 (action table), plan 01 M3 (router). Credit Ardia and Stedding with their notices.

## Machine and worktree

0. Step 0 in the README first: the main checkout is pulled and its base build approved by the maintainer.
- Whichever Mac has a free slot after launch: `git worktree add -b feat/power-<m> <path> main`, then `devutils/rac/worktree.sh setup` (or `setup <checkout>` to clone a built tree, if the maintainer OKs it, D6). One worktree per milestone.
- Air Traffic Control tests send links through UI's `open-urls` harness verb. No step changes the default browser; the maintainer checks the real default-browser flow by hand on a second macOS user.
- Never touch real profiles or real agent configs.

## Power adds to the verification standard

Unit tests for `SitePattern`, the strip table (including cases that must not change), and Ardia's naming cases ported one for one; shots in two spaces and incognito where it applies; motion videos with Reduce Motion on and off; a net log showing no requests; zero Boosts means no script and no file read at startup.

## Coordination

- No second action table: add fields and rows to Core's table (03 M1). M0 waits for it.
- M3 waits for UI's router (01 M3). M5 needs its own go-ahead after a Helium diff check.
- Shared files: `browser_shortcut_metadata.cc`, `spaces/commands.patch`, `browser_commands.cc`, the site control center (UI, Core), omnibox and bangs files (UI, Helium). Every per-site entry goes through site controls placed by UI.
- Nothing merges during Ship's freeze; every upstream hook waits for the sync and base rebuild.
- With AI off, no AI button (the group "Name with AI" button exists only with AI on).

## First milestone

M0 (3 to 5 agent-days), once Core's table has landed:

1. Write `rac::SitePattern` in `chrome/browser/rac/site_pattern/`: host and subdomain matching, "URL contains", case-insensitive, using Chromium's registrable-domain helper.
2. Add "default shortcut" and "menu label" fields to the table; make Helium's shortcut metadata read them through one hook, replacing the per-command hunks in `spaces/commands.patch`. This rewrites merged work: re-test every space shortcut.
3. Unit tests and a screenshot of the shortcuts page. Expect about 2 hunks replacing 4.

Then M1: clean-link copy through `rac::CleanLink()`, Copy as Markdown, the Arc keymap rows, and group naming.

## Done means

Each milestone's acceptance in plan 07 passes: for example `https://x.com/a?utm_source=y&id=3#c` copies as `https://x.com/a?id=3#c`, three GitHub PR tabs name a group "GitHub", and Boosts apply before first paint, survive restart, and work in incognito. Each PR has proof and its hunk delta.
