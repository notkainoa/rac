# Cross-plan rulings

The seven plans were revised against these rulings on 2026-10-27. Where a plan and a ruling disagree, the ruling wins. Decision ids here are the plan ids; see decisions.md for the D-numbers.


1. Calendar. Don't assume any work starts before the maintainer approves the plans. Write milestones as "week N after approval", and give a target date only against two fixed anchors: Arc's shutdown on 2026-12-22, and a hard stop for the launch build on 2026-12-15. Every milestone states which Chromium version it targets (154 today; 156 after the Helium 0.20.1.1 sync). Work that touches hot files shared with Helium waits for the sync. Work in rac-owned files may be built on 154 and rebased. Plan 06 owns the sync and the launch calendar. Other plans reference plan 06's weeks instead of inventing their own. The hop to Chromium 157 is optional and plan 06 decides it. Count the base-tree rebuild after the sync as an explicit dependency for every worktree.
2. One action table. Plan 03 owns the single rac action/command table, with surfaces and risk classes. Plan 07 adds shortcut and label fields to it and keeps only its SitePattern matcher. Plans 01 and 05 consume it. No second or third table.
3. Command bar UI technology: native Views. Plan 03's "where each part lives" table must say "command bar: Views; rows are C++ from the action table". The one-frame open is a measured gate, not a guarantee.
4. Clear and archive. Plan 01 owns Clear, the MayClear rule (which tabs Clear spares, with reasons), the archive store, and auto-archive (later, off by default; keep an imported Arc user's own setting). Before launch, ship Clear with Undo via recently-closed restore. The persistent archive comes after launch. Plans 04 and 07 reference plan 01 and own none of these.
5. Agent tabs. Plan 05 decides what an agent's workspace is (05-D3, pending its rendering spike; resolved as an Agents section in the sidebar, see decisions.md C1). Plan 01 draws it in the sidebar, scheduled together with plan 05's write tier, not last.
6. Cmd+S and edge reveal. Plan 06 owns porting the sidebar-reveal patches onto Helium 0.20's overlay during the sync. Plan 01 owns behavior (dwell and grace times, reconciled with Helium 0.20's 150 ms hide grace and 3 s exit grace). Plan 02 owns motion. One set of token names: plan 02's.
7. Debug doors. The decision lives in plan 05 (05-D6). Plan 03 references it. Corrected fact: chrome://inspect remote debugging is off by default, needs a user toggle, and each connection needs approval (remote_debugging_server.cc). Describe the risk accurately.
8. The outside-agent door. Plan 03 provides:
   - a per-profile socket that exists only while the switch is on;
   - per-client tokens that can be revoked;
   - the split of AgentController, the guard, and the MCP server out of AiService, as a costed task with an estimate.
   Plan 05 owns the policy, including what replaces "named sites / the user's own words" for clients that never send chat messages.
9. Warm agent. One decision, in plan 03 (03-D3): one warm agent per profile, 5-minute idle cap. Plan 05 references it.
10. Moving rac-owned source out of patches into a plain folder. One decision, in plan 06 (06-D12). Plan 03 references it.
11. Patch-surface metric. Count net-diff hunks in upstream files, plus dry-run failures per Helium sync. Plan 03 defines it and sets a realistic target with a per-group breakdown. Plan 06 runs it as a check.
12. Media controls belong to plan 01.
13. The Keychain silent-reset fix belongs to plan 04, and plan 06 lists it as a launch gate.
14. Arc profile mapping. Cost "Arc profile -> rac profile, Arc space -> rac space" as an explicit option. It may be the cheapest pre-12-22 path.
15. VISION. Keep "AI off costs nothing" as it is. Add a separate, scoped promise for the outside-agent door: its own switch, off by default, and when off it costs nothing. Show "Outside agents: on" next to the AI switch whenever the door is on. Changes to VISION.md need the maintainer's sign-off, so list them as decisions.
16. With AI off, no AI buttons, rows, or labels appear anywhere, including the command bar. Many Arc refugees explicitly want "no AI buttons" (an Arc-alternative wishlist tweet, 2026-10-27). Make it an acceptance check wherever AI surfaces are touched.
17. Installed web apps (PWA windows) join the surface matrix. Nobody has tested whether rac's look and sidebar patches break them. Plan 01's first milestone checks them.
18. Size and decisions. Aim for about 4,500 words. At most about 8 decisions per plan. A decision another plan owns is referenced ("see 03-D3"), never repeated. Every decision is answerable in one line.
