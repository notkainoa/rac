# Thread brief: Core (rac core and agents)

> **DRAFT: do not launch until the maintainer approves the plans.**

Follow ["Every thread"](README.md#every-thread) in the README: reading, step 0, workflow stages, verification standard, and hard constraints. This brief adds only what is specific to Core.

## Goal

Before launch: close the agent's `auto` hole and prove it, then build the action table. After launch: the opt-in door for outside agents (MCP and a `rac` CLI), the warm agent, and the agent workspace. No helper, no port.

## Owns

Plan 05 M0 (launch gate: taint rule, fail-closed defaults, page-text marking, debug doors, dev switches; G4 to G7, G15 part) and plan 03 M0 and M1. After launch: 03 M2 with 05 M1 as one door milestone, 03 M3, 05 M2 and M3, then 03 M4 (thinning) last.

## Decisions it depends on

- **Group A:** D1, D2, D9a/b/c, D17 (hunk budget), D19 (taint rule), D20 (debug doors), D21 (no server, before 03 M1), D22.
- **By milestone:** D12a/b (door with AI off, and VISION wording), D23 (rows, W2), D24 to D26 (door), D27 (warm agent), D56, D59, D46 (write tier waits for Data's partition).

## Plan-specific reading

`docs/internals/ai.md`, `patches/rac/agent/`, plans 05, 03, 00, and 06 (calendar, sync).

## Machine and worktree

0. Step 0 in the README first: the main checkout is pulled and its base build approved by the maintainer. The base then includes agent patches 13 to 17.
- The base Mac, one worktree at a time: `git worktree add -b feat/agent-<m> <path> main` or `feat/core-<m>`, then `devutils/rac/worktree.sh setup`.
- After the sync, worktrees may clone the sync worktree's 156 tree with `worktree.sh setup <checkout>` if the maintainer OKs it (D6).
- Run evals on throwaway profiles with test accounts; ask before spending the maintainer's API keys. `claude mcp add` edits real configs, so use a throwaway `HOME`.
- In non-release builds, the relay never launches rac without an explicit `--user-data-dir` (taken from `RAC_USER_DATA_DIR`). Tests of "relay with rac closed" start rac through the harness, never `open`.

## Core adds to the verification standard

Tier 1 evals green within the false-card budget; a fixture per trust-root row; AI-off set 1; with AI and the door off, `ps` and `lsof` in a fresh profile show no rac service, child, or socket; videos of approval flows.

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
4. A guard next to the debug doors: non-release builds refuse to start on the default `me.kainoa.rac` folder.
5. Run tier 1 evals; report false-card rate.
6. In parallel, 03 M0 spikes: where Claude Code's 25 s startup goes, and the door pass/fail table (Claude Code, Codex, Cursor, OpenCode; socket path; relay with rac closed, using an explicit `--user-data-dir`).

After the sync: debug doors and release gating of dev switches, with Ship.

## Done means

G4 to G7 are green with evidence and the `ai.md` table matches behavior. Later: Claude Code can read shared tabs through the door with AI off, and "Outside agents: on" shows while it is on.
