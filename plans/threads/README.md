# Thread briefs

Draft briefs for the five build threads in the [master plan's thread map](../00-master-plan.md#thread-map). Every brief is marked DRAFT and must not launch until the maintainer approves the plans and answers group A of [decisions.md](../decisions.md).

| Thread | Owns | Starts when | Blocked on decisions | Machine |
| --- | --- | --- | --- | --- |
| [Ship](ship.md) | Plan 06 M0 to M5, the sync, the freeze, launch gates G9 to G14, later the beta channel and plain-folder move | W1, right after approval (Depot signup on day 1) | D1, D2, D4, D5, D6, D9, D11; later D3, D7, D8, D10, D17, D18, D58 | The Mac from D5 for the sync (`sync/helium-0.20.1.1`); Depot for releases; light worktrees for CI and site |
| [UI](ui.md) | Plan 01 M0 to M4 and M6 (M5 with Core), plan 02 M0 to M5, the harness | W1 | D1, D2, D5, D9, D14, D16, D22; later D13, D23, D28 to D40 | The base Mac, at most two worktrees |
| [Core](core.md) | Plan 05 M0 (launch gate), plan 03 M0 and M1; after launch the door, warm agent, 05 M2 and M3, thinning | W1 | D1, D2, D9, D19, D20, D21, D22; later D12, D23 to D27, D46, D56, D59 | The base Mac, one worktree at a time |
| [Data](data.md) | Plan 04 M0, M1, and M2 if ready; after launch partitions and the AI store | W1 (new files only during the freeze) | D1, D2, D9, D41, D42; later D43 to D47, D55 | The base Mac, one worktree (light unit-test build) |
| [Power](power.md) | Plan 07 M0 to M5 | After launch (W7 on), once Core's table and UI's router land | D9, D31, D48; later D49 to D54 | Whichever Mac has a free slot |

**How launching works.** The maintainer approves the plans and answers group A. Then each thread is a T3 Code thread in its own worktree, started from its brief plus the master plan's thread map. Ship, UI, Core, and Data start at W1. Power starts after launch. The maintainer approves every merge.
