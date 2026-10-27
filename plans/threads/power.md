# Thread brief: Power (power features)

> **DRAFT: do not launch until the maintainer approves the plans.**

## Goal

After launch, add what Arc refugees reach for daily: clean links, Copy as Markdown, group naming, Boosts, Air Traffic Control (link routing), and bangs, with no second action table and no network calls.

## Owns

Plan 07 M0 to M5. Before launch, only 07 M1's pure logic (the strip table, the naming rule) may be written, with unit tests and no build slot.

## Decisions it depends on

- **Before it starts:** D9, D48 (order), D31 (shortcuts; taking Opt+Cmd+N needs the maintainer's OK).
- **By milestone:** D49 and D50 (M1), D54 (Boosts, before M2; VISION wording), D51 (M3), D52 (M5 go or no-go), D53 (themes vs space colors), D12, D17.

## Read first

`AGENTS.md`, `VISION.md`, `plans/07-power-features.md`, `docs/internals/bangs.md`, `plans/00-master-plan.md`, plan 03 M1 (action table), plan 01 M3 (router). Credit Ardia and Stedding with their notices.

## Machine and worktree

Whichever Mac has a free slot after launch: `git worktree add -b feat/power-<m> <path> main`, then `devutils/rac/worktree.sh setup`; one worktree per milestone. Testing Air Traffic Control means changing the default browser: use a second macOS user, or ask first and restore it afterwards. Never touch real profiles or real agent configs.

## How to use multi-agent Claude Code workflows inside the thread

Run each milestone through five stages.

1. **Understand.** Read-only subagents (Haiku or Sonnet) read the plan section, the files it touches, and AGENTS.md, and return a short map.
2. **Design.** Opus writes a one-page design (interfaces, hunk budget, test plan) before any code.
3. **Implement.** Hard architecture and security go to Opus. Routine, scoped code and tests go to Sonnet or a strong open-weight model (`kimi-k3`, `glm-5.3`, `deepseek-v4-pro`, `minimax-m3`). UI work goes to Claude Opus (routine UI to Sonnet), never open-weight models.
4. **Verify.** You build, run, and capture. A Haiku subagent may run tests and summarize.
5. **Review.** Before every PR, a fresh Opus reviewer that hasn't seen the design tries to break the diff (attacks, edge cases, missed surfaces, hunk count), then run `/code-review`. Fix or answer every finding. Check subagent output before building on it.

## Verification standard

- Build and run it yourself: `source dev.sh && he build`, then `devutils/rac/worktree.sh run --rac-window-screenshot=/abs/path.png`. Wait for real pixels.
- Answer AGENTS.md "Cover every surface" item by item. Screenshot matrix: sidebar full, hidden, and edge reveal; light and dark; space themes; multiple windows; incognito; split view; an installed web-app (PWA) window; reduced motion; AI off (no AI button, row, or label).
- Short videos for motion. Focused unit tests only. `he validate series` after touching `patches/series`.
- Every PR states its net-diff hunk change (D17) and attaches proof with `gh pr create --attach './shot.png#caption'`. Never commit screenshots or videos.
- No PR unless the maintainer asks, or D9 grants standing permission. The maintainer approves every merge.
- Power adds: unit tests for `SitePattern`, the strip table (including cases that must not change), and Ardia's naming cases ported one for one; shots in two spaces and incognito where it applies; motion videos with Reduce Motion on and off; a net log showing no requests; zero Boosts means no script and no file read at startup.

## Hard constraints from AGENTS.md

- Never push to, open PRs against, or file issues on `imputnet` or `ungoogled-software`.
- Never edit `helium-chromium/`, `patches/helium/`, `patches/rebel/`, or `patches/ungoogled-chromium/`.
- `rac_version.txt` only goes up. The signing key and feed URL never change.
- Never take the foreground (no `open`, no `he run`, no foreground automation). Never use a real profile.
- No full build, `he reset`, or deleting `build/` without approval (D6 names the allowed ones). If a worktree build shows tens of thousands of steps, stop.

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
