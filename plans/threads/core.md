# Thread brief: Core (rac core and agents)

> **DRAFT: do not launch until the maintainer approves the plans.**

## Goal

Before launch: close the agent's `auto` hole and prove it, then build the action table. After launch: the opt-in door for outside agents (MCP and a `rac` CLI), the warm agent, and the agent workspace. No helper, no port.

## Owns

Plan 05 M0 (launch gate: taint rule, fail-closed defaults, page-text marking, debug doors, dev switches; G4 to G7, G15 part) and plan 03 M0 and M1. After launch: 03 M2 with 05 M1 as one door milestone, 03 M3, 05 M2 and M3, then 03 M4 (thinning) last.

## Decisions it depends on

- **Before it starts:** D1, D2, D9, D19 (taint rule), D20 (debug doors), D21 (no server, before 03 M1), D22.
- **By milestone:** D17 (hunk budget), D12 (door and VISION wording), D23 (rows, W2), D24 to D26 (door), D27 (warm agent), D56, D59, D46 (write tier waits for Data's partition).

## Read first

`AGENTS.md`, `VISION.md`, `docs/internals/ai.md`, `patches/rac/agent/`, plans 05, 03, 00, and 06 (calendar, sync).

## Machine and worktree

The base Mac, one worktree at a time: `git worktree add -b feat/agent-<m> <path> main` or `feat/core-<m>`, then `devutils/rac/worktree.sh setup`. The first 154 build is larger than usual (the base tree predates agent patches 13 to 17); ask before it. Run evals on throwaway profiles with test accounts; ask before spending the maintainer's API keys. `claude mcp add` edits real configs, so use a throwaway `HOME`.

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
- Core adds: tier 1 evals green within the false-card budget; a fixture per trust-root row; AI-off set 1; with AI and the door off, `ps` and `lsof` in a fresh profile show no rac service, child, or socket; videos of approval flows.

## Hard constraints from AGENTS.md

- Never push to, open PRs against, or file issues on `imputnet` or `ungoogled-software`.
- Never edit `helium-chromium/`, `patches/helium/`, `patches/rebel/`, or `patches/ungoogled-chromium/`.
- `rac_version.txt` only goes up. The signing key and feed URL never change.
- Never take the foreground (no `open`, no `he run`, no foreground automation). Never use a real profile.
- No full build, `he reset`, or deleting `build/` without approval (D6 names the allowed ones). If a worktree build shows tens of thousands of steps, stop.

## Coordination

- Every call enters `AgentController::HandleToolCall` and the guard. No policy at the MCP layer, no raw CDP.
- Land the action table first, with plan 07's fields already in it, so Power only adds rows. After 03 M1's one-hook registries exist, others register there.
- Shared files: `rac_actions.{h,cc}` (UI, Power), the profile factory list, prefs and strings registries, `chrome/BUILD.gn` and `parts.py` (Ship), `chrome/browser/rac/ai/` (Data), `browser_navigator.cc` and session restore (Data; take turns), `ai.md`.
- Nothing under `patches/` merges before Ship's sync. Rebase onto 156 after it; debug doors are built on 156. Thinning touches a group only when nobody has an open PR on it.
- UI draws your screens. Give them the table schema in W1 to W2.
- Ask before more than 10 new upstream hunks or a new signed part beyond the relay.

## First milestone

05 M0 on 154, in rac-owned files (W1 to W3):

1. The taint rule (D19): read set per conversation, escalation at two origins, the card naming destination and sites, submit cards showing typed values except passwords.
2. Fail closed: `level_` starts `kAsk`, unknown level parses to `ask`, malformed site rule becomes Never, one test each.
3. Mark page text for every model: tool-named boundaries, escaped fake markers.
4. Run tier 1 evals; report false-card rate.
5. In parallel, 03 M0 spikes: where Claude Code's 25 s startup goes, and the door pass/fail table (Claude Code, Codex, Cursor, OpenCode; socket path; relay with rac closed).

After the sync: debug doors and release gating of dev switches, with Ship.

## Done means

G4 to G7 are green with evidence and the `ai.md` table matches behavior. Later: Claude Code can read shared tabs through the door with AI off, and "Outside agents: on" shows while it is on.
