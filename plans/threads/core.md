# Thread brief: Core (rac core and agents)

> **DRAFT: do not launch until the maintainer approves the plans.**

Follow ["Every thread"](README.md#every-thread) in the README: reading, step 0, streams, the build queue, moving to 156, workflow stages, verification standard, and hard constraints. This brief adds only what is specific to Core.

## Goal

Before launch: close the agent's `auto` hole and prove it, with every piece merged by day 13 (G4 to G7). Start the action table. After launch: the opt-in door for outside agents (MCP and a `rac` CLI, days 14 to 30), the warm agent, and the agent workspace. No helper, no port.

## Owns

Plan 05 M0 (launch gate: taint rule, fail-closed defaults, page-text marking, debug doors, dev switches; G4 to G7, G15 part) and plan 03 M0 and M1. After launch: 03 M2 with 05 M1 as one door milestone, 03 M3, 05 M2 and M3, then 03 M4 (thinning) last.

## Decisions it depends on

- **Group A:** D1, D2, D9a/b/c, D17 (hunk budget), D19 (taint rule), D20 (debug doors), D21 (no server), D22, D62, D63.
- **By day:** D23 (day 3, rows), D12a/b and D24 to D26 (day 14, the door), D27 (day 22, warm agent), D56, D59, D46 (the write tier waits for Data's partition).

## Plan-specific reading

`docs/internals/ai.md`, `patches/rac/agent/`, plans 05, 03, 00, and 06 (calendar, sync).

## Streams

| Stream | Branch | Days | Work | Main files |
| --- | --- | --- | --- | --- |
| `guard` | `feat/agent-guard` | 0-10 | 05 M0 tasks 1 to 4 and 9: the taint rule, fail-closed defaults, page-text marking, copy fixes. Opus. After launch it becomes the door stream | `AgentController`, the guard, prompt building |
| `evals` | `feat/agent-evals` | 0-10 | Tier 1 fixtures and runner, AI-off test set 1. Fixtures split among three or four helpers. Runs against `guard`'s build | Eval fixtures and runner, AI-off tests. No guard code |
| `doors` | `feat/agent-doors` | 4-10 | 05 M0 tasks 5 and 6 on the 156 base: refuse the debug doors on the default profile, and gate dev switches out of release builds with Ship and the other plans | Startup switch checks, GN args with Ship |
| `table` | `feat/core-table` | 0-22 | 03 M0 spikes (days 0-2, no patches). Then 03 M1 tasks 1 and 3: the static action table with plan 07's fields, and `tools/list` from it. The core split (task 2) starts only after `guard` merges | `rac_actions.{h,cc}`; later `RacCoreService` |

The split waits for `guard` because both move or edit the same agent files. That is the one serial step inside Core.

## Machine and worktree

- The Air, through the queue. `guard` and `table` start as light worktrees on 154 in rac-owned files. `doors` starts on the 156 base about day 4. `guard` moves to the 156 base once it is announced.
- `evals` runs against `guard`'s built binary through the queue's run slots. It needs no build tree of its own unless it adds C++ tests.
- Run evals on throwaway profiles with test accounts; ask before spending the maintainer's API keys. `claude mcp add` edits real configs, so use a throwaway `HOME`.
- In non-release builds, the relay never launches rac without an explicit `--user-data-dir` (taken from `RAC_USER_DATA_DIR`). Tests of "relay with rac closed" start rac through the harness, never `open`.

## Core adds to the verification standard

Tier 1 evals green within the false-card budget; a fixture per trust-root row; AI-off set 1; with AI and the door off, `ps` and `lsof` in a fresh profile show no rac service, child, or socket; videos of approval flows.

## Coordination

- Every call enters `AgentController::HandleToolCall` and the guard. No policy at the MCP layer, no raw CDP.
- Land the action table with plan 07's fields already in it, so Power only adds rows. Publish its schema to UI `bar` and Power `logic` on day 1.
- Shared files: `rac_actions.{h,cc}` (UI, Power), the profile factory list, prefs and strings registries, `chrome/BUILD.gn` and `parts.py` (Ship), `chrome/browser/rac/ai/` (Data), `browser_navigator.cc` and session restore (Data; take turns), `ai.md`.
- Copy fixes for G7 go through Ship's `site` stream for the site, and through UI `import` for onboarding.
- Nothing under `patches/` merges before the sync. In Ship's merge order, `guard`, `evals`, and `doors` are launch gates. `table` merges after the launch build fires.
- Thinning touches a group only when nobody has an open PR on it. Ask before more than 10 new upstream hunks or a new signed part beyond the relay.

## First steps

Day 0, in parallel:

1. `guard`: design the taint rule (D19): read set per conversation, escalation at two origins, the card naming destination and sites, submit cards showing typed values except passwords. Then fail closed: `level_` starts `kAsk`, unknown level parses to `ask`, malformed site rule becomes Never, one test each. Then page-text marking.
2. `evals`: list every tier 1 variant, split them among helpers, and write fixtures. Write AI-off set 1.
3. `table`: the 03 M0 spikes: where Claude Code's 25 s startup goes, and the door pass/fail table (Claude Code, Codex, Cursor, OpenCode; socket path; relay with rac closed, using an explicit `--user-data-dir`). Then the table schema.
4. `doors` waits for the 156 base, about day 4. Until then its lead reads the 156 switch code in the sync worktree, read only, and writes the design.

## Done means

G4 to G7 are green with evidence and the `ai.md` table matches behavior. Later: Claude Code can read shared tabs through the door with AI off, and "Outside agents: on" shows while it is on.
