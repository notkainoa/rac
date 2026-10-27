# Digest: chromium-agent-internals.md (Chrome's built-in agent stack)

## In plain English

Chrome has a built-in agent stack. Google uses it so Gemini can click and type
on sites. It has three layers: a page outline a model can read, page actions,
and a Gemini panel. rac uses the bottom two and skips the panel; that was right.
Chrome's task engine refuses to act when Google's malware check is off, and
Helium always turns it off. Chrome's on-device model cannot run in rac. The code
changes about seven times a day, mostly in parts rac skips. Websites can publish
tools for agents; rac can support them cheaply. rac's real work is a few
Chromium breaks and one safety gap at `auto`.

## Key facts

Keys: **C:** rac's read-only tree (Chromium 154.0.8037.92, Helium 0.18.2.1);
**U156/U157/UM:** upstream `156.0.8078.48`, `157.0.8103.15`, main `edd1071`;
**R:** this worktree; **H:** vendored Helium; **HL:** Helium clone `f29a259`.
FACT = primary source, CLAIM = vendor/third-party report, INFERENCE = reasoning.

### Stack and release (FACT)

- Layers: **actor** (`C:chrome/browser/actor`, `C:chrome/renderer/actor`,
  `C:components/actor`), **Glic** (`C:chrome/browser/glic`), **APC** (Blink
  `content_extraction` + `components/optimization_guide/content/browser`),
  origin gating (`components/origin_gating`), WebMCP
  (`third_party/blink/renderer/core/script_tools`), built-in AI
  (`chrome/browser/ai`, `services/on_device_model`).
- Versions, 2026-10-25: rac reads 154.0.8037.92; Stable 156.0.8078.48; Beta
  157.0.8103.15; Canary 158.0.8124.0. Chromium branches every two weeks from
  M153: 153 08-18, 154 08-31, 155 09-14, 156 09-29, 157 10-13; 152 07-27, 151
  06-29.
- License: client code BSD-3-Clause. Planner, critic, and injection classifier
  are Google-hosted and proprietary
  ([Google, 2025-12-08](https://blog.google/security/architecting-security-for-agentic/)).
  On-device library `optimization_guide_internal` is closed;
  `build_with_internal_optimization_guide = is_chrome_branded`, false for public
  builds (`C:components/optimization_guide/features.gni:41-45`).
- Glic code by 2024-11-27; first actor commit 2025-03-17. Actor on desktop and
  Android; `kGlic` defaults on for Mac, Windows, ChromeOS, Android. Auto browse
  sells to US Google AI Pro/Ultra
  ([9to5Google](https://9to5google.com/2026/01/28/chrome-gemini-auto-browse/));
  reported $19.99/$249.99 a month and 20/200 tasks a day (CLAIM).

### Size and churn

Recount (`.cc`/`.h`; test = filename contains `test`), authoritative over the
original unreproducible method (off by up to 40% for `components/actor`):
`chrome/browser/actor` 32,510 code / 40,253 test; `chrome/renderer/actor`
5,823/121; `components/actor` 3,009/1,124; Glic 75,535/74,131; Blink APC
6,052/11,112; browser APC 6,032/9,947; WebMCP 1,676/2,037; `chrome/browser/ai`
7,211/8,784; `services/on_device_model` 9,362/2,872.

In 55 days after the 154 branch: 405 commits in `chrome/browser/actor`, 756 in
Glic, 53 in `components/actor`, 27 in WebMCP, 19 in Blink APC, 11 in
`chrome/renderer/actor`, 2 in `chrome/common/actor.mojom` — about 7 actor and 14
Glic a day. The big M157/M158 refactors are mostly in layers rac skips
(`ActorSurface` replacing `TabHandle`, `ToolRegistry`, transport,
tool-directory moves).

### Mechanics (FACT unless tagged)

- **Glic** is a WebUI hosting a guest `<webview>` of
  `https://gemini.google.com/glic` (`kGlicGuestURL`,
  `C:chrome/common/chrome_features.cc:689-691`) over a 2,391-line `glic.mojom`.
  `ActorHandler` (`:893-1015`) exposes
  `PerformActions(array<uint8> actions_proto)` (`:930`). **The model never runs
  in the browser.**
- Glic needs a signed-in Google account (`glic_enabling.cc:442`). ungoogled has
  no sign-in and domain substitution rewrites `chrome_features.cc`
  (`R:helium-chromium/domain_substitution.list:2406`); Helium also strips its
  context-menu entries. Glic is compiled in but unreachable in rac. INFERENCE.
- **Task states:** Created, Acting, Reflecting, PausedByActor, PausedByUser,
  WaitingOnUser, Cancelled, Finished, Failed (`actor_task.h:140-188`).
- **Engine:** Init → StartAction → CreateAndVerify → UiPreInvoke → ToolInvoke →
  UiPostInvoke → Complete (`execution_engine.cc:803-815`). Browser tools stay in
  the browser; page tools cross via `ChromeRenderFrame::InvokeTool`
  (`chrome_render_frame_observer.cc:685-699`).
- **Actions:** 25 kinds in the server `Actions` proto
  (`actions_data.proto:483-535`); only 8 run in the renderer: click,
  drag_and_release, mouse_move, scroll, select, type, script_tool, scroll_to.
- **ToolRegistry:** 40 IDs (0–39) on main, 23 at U157, from M157
  (`tool_definition.h:19-101`), each with a JSON Schema; effectively MCP-shaped
  (INFERENCE). Names include `navigate`, `click`, `type`, `switch_tab`,
  `open_url`, `scroll`, `select_option`, `go_back`. `open_url` is only on main
  (`3cc2ba10`, 2026-10-23); `open_known_page` is at U157; `switch_tab` and
  `perform_search` exist at U156.
- **Headless:** `ActorSurface` landed 2026-09-28T20:30Z (`31cd13c8`), before the
  M156 branch; `HeadlessWebContentsManager` followed (`27a6b536`, M157).
- **APC** walks Blink's **layout tree**, not the DOM, so only rendered content
  appears. Modes `kDefault` and `kActionableElements` (adds geometry, z-order,
  interactivity). Options include `on_critical_path`, `include_same_site_only`,
  `node_id_allowlist`, an ad filter, and password/payment/OTP redaction boxes.
- **WebMCP:** `document.modelContext.registerTool/getTools/executeTool` plus
  `<form toolname tooldescription>`. Origin trial Chrome 149–156 (FACT,
  chromestatus 5117755740913664; no ship milestone); still `experimental` at
  U157/UM. APC already carries per-frame `script_tools`
  (`ai_page_content.mojom:439`), and **rac drops them** (no `script_tool` use in
  `R:patches/rac/`). The actor can invoke one via `ScriptToolAction` over
  `InvokeTool` (`actor.mojom:135-150`).

### Safety model (Chrome vs rac)

| Layer | Chrome 154 + Google | rac today |
| --- | --- | --- |
| Who acts, which sites | Signed-in eligible account, country/locale, enterprise policy; origin gating has **19 ordered predicates** over nav request, nav response, page action (`execution_engine.cc:683-760`). New-origin confirm off in 154, **on by default from M158** (`8799124`, 2026-10-19). FACT | AI on, browser control on, regular profile; named origins plus `always`/`never`; at `auto`, cross-site navigation is free. |
| Safe Browsing | Predicate 9 of 19 blocks nav requests and page actions when off (`:423-437`); about:blank, localhost, and `--disable-actor-safety-checks` are decided earlier. | `safe_browsing_mode=0` in dev and release flags sets `SAFE_BROWSING_AVAILABLE=false`; Chrome's engine would block nearly everything. |
| Lists, sensitive sites | Google-served `GLIC_ACTION_PAGE_BLOCK` hints, fails open if missing; per-site cache planned M158; JSON `from`→`to` allow/block lists via component updater (`safety_list_manager.h:20-75`). | No list; word lists (buy, send, delete…) plus control types. Helium allows only CRLSet and Widevine components, so static lists never download. |
| Model URLs, critic, injection | URLs limited to "known, public URLs"; "User Alignment Critic" sees only action metadata; server classifier runs beside the planner and "cannot flag everything" (CLAIM). | URL must come from a user message or a snapshot link; critic only at `careful`, metadata only; no classifier; page text is nonce-wrapped and labelled untrusted. |
| Time-of-use | `observed_target` plus `kGlicActorToctouValidation`, **off upstream at 154/U156/U157/UM**. | rac **flips it on** (`03-actions.patch:2139-2148`); renderer re-check at `tool_base.cc:636-750`. |
| Secrets, red team | `attempt_login`/autofill: user picks, browser fills, model never sees values; automated attack sites; bug bounty to $20,000 (CLAIM). | Password/payment fields always risky; values redacted; no evals or red team (brief). |

Also: lookalike-domain block, localhost sensitive, non-localhost IPs blocked,
dangerous MIME types blocked, File System Access picker blocked, cross-site
iframe screenshots redacted (`kCrossSite`), APC password/payment/OTP redaction.
`--actor-sensitive-sites=` (M155) is a local list, **not in 154**.

### rac's actual usage and the coming breaks

rac does **not** use `ActorKeyedService`, `ActorTask`, `ExecutionEngine`, origin
gating, the actor UI, or Glic; it drives renderer tools directly ("No Glic",
`C:chrome/browser/rac/agent/renderer_tools.h:25`). Of 238 non-test rac-created
C++ files, 91 lines touch `actor::`, `optimization_guide::`,
`page_content_annotations::`, or `AIPageContent`: 36 in `renderer_tools.cc`, 17
in `semantic_validator.{h,cc}`, 8 in `apc_extract.{h,cc}`.

Stable through main: `InvokeTool`/`CancelTool`, click/type/select `ToolAction`s,
`ObservedToolTarget`, actor helpers, `PageSettledMonitor`. Two **M158 compile
breaks**:

1. `ScrollAction(ScrollDirection, float distance)` becomes
   `ScrollDirectionPhysical direction; ScrollAmount amount` (distance or
   granularity union), commit 2026-10-16; unchanged at U156/U157. `execution_id`
   becomes `ToolInvocationToken`; rac does not set it.
2. `AIPageContentResultOrError` goes from `expected<…, std::string>` to
   `expected<…, AIPageContentError{status, message}>`, commit 2026-10-16; rac
   uses it in 10 places across 9 files, at least 2 passing `.error()` as a string.

`common_quality_data.proto` changed 128 lines 154→main; the only removals are
`gemini_in_chrome_page_metadata`, `screenshot_info`, and
`CLICKABILITY_REASON_MOUSE_HOVER`, none used by rac. INFERENCE.

rac's agent patches edit **21 upstream files, 58 hunks, ~207 lines** (198 added,
9 removed). The Chromium-agent subset is 13 files, 40 hunks, ~158 lines in
renderer `type_tool`, `key_dispatcher`, `click_dispatcher`, `tool_base`,
`tool_executor`, `BUILD.gn`, `actor.mojom`, `chrome_features.cc`,
`chrome_render_frame_observer.cc`, `web_local_frame_impl.cc`, and throttles. The
other 8 are hooks in browser-client, download, web-contents delegate, prefs, and
four `BUILD.gn` files. Sync-cost plans must use 21 files, not the earlier 13.

Text-only `patch --dry-run`: all clean at 154. From 156, `key_dispatcher.cc`
fails 1 of 7, `click_dispatcher.cc` 1 of 4, `tool_base.cc` 1 of 1
(`ExecutionObservationDelay()` was removed 2026-09-02), and
`chrome_render_frame_observer.cc` 1 of 2. `type_tool.cc` (332 upstream lines
changed), `tool_base.h`, `tool_executor.cc`, and `actor.mojom` stay clean.

Risk: **low** for rac's layer — about 4 failed hunks and 2 compile fixes to
M158, roughly 1–2 days. **Medium** for APC meaning drift because tests use
synthetic protos. **High** if rac adopted `ExecutionEngine`, `ActorKeyedService`,
or Glic. Tail risk: if Helium/ungoogled disables `kGlicActor` to save idle
objects, the renderer `CHECK` (`tool_executor.cc:45`) crashes rac's agent; keep
the feature on or remove the `CHECK`.

### Motion (exact, from code)

| Element | Parameters |
| --- | --- |
| Acting-page glow | `box-shadow: inset 0 0 35px 12px #4C8DF6`; opacity 0.6 → 0 → 0 → 0.6 over **4000 ms, infinite**, `cubic-bezier(0.33,0,0.67,1)` with linear hold. **No reduced-motion guard.** |
| Magic cursor | 24 px SVG, two blue shadows; 1.5 px/ms, clamped 50–300 ms; `cubic-bezier(0.6,0,0.4,1)`; reduced motion 0 ms |
| Cursor click | 400 ms `ease-out`; at 40%, `scale(0.85) translateY(2px)` |
| Cursor thinking | 750 ms intro, then 3200 ms infinite loop (750 ms per 4 px, 100 ms holds); off under reduced motion |
| Cursor fade | 200 ms `ease` |
| Glic context border | 500 ms up, 1500 ms hold, 1000 ms down (EASE_OUT, then EASE_IN_OUT_2); radius 12 |
| Glic animated effect | opacity in 500 ms, out 200 ms; reduced motion skips the cycle, holds still, fades in 200 ms |
| Glic selection | 250 ms fade, 250 ms bounds, `FAST_OUT_SLOW_IN` |
| Shared-tab underline | 3000 ms cycle |
| Debounce | 25 ms hover on overlay/handoff; 500 ms profile-wide UI; finished task listed 30 s |

### Storage, timing, idle cost

- Conversations, plans, and task state live on Google servers and leave the
  machine by design. Page context (APC, viewport screenshot, inner text, PDF
  bytes) is sent per request.
- Actor journal in memory; `--actor-trace-path` writes a Perfetto-style trace
  (`AggregatedJournal`, parser `parse_actor_trace.py`). Helium removed
  `chrome://actor-internals` in 0.19.3.1.
- PCES (memory + SQLite) is off by default and disabled by ungoogled. The
  on-device model would sit at `<user data>/OptGuideOnDeviceModel`. Glic/actor
  prefs are `Preferences` JSON.
- **In rac:** none of Google's flows run. rac calls `GetAIPageContent` directly,
  serializes locally, and sends text only to the user's chosen provider.
- **AI-off idle cost:** `kGlicActor` is on by default, so every regular profile
  builds an `ActorKeyedService` (UI state manager, blocklist lookup, download
  observer), and every tab builds `ActorTabData` and `ActorUiTabController`.
  They sit idle because ungoogled empties `GetTaskFromTab`. Small but
  **unmeasured**. INFERENCE for size.
- Timing: page stability 1–4 s; observation delay 10 s; LCP wait 1 s; page tools
  30 s; click delay 5 ms; script tools 30 s, or 5 s across documents.
- `TabObservation` = APC + screenshot, each voted Skipped/Requested/Required per
  action; targets are APC `dom_node_id` or a DIP coordinate. rac's non-reused
  `e{N}` refs are more robust. INFERENCE.

### Outside agents and built-in AI

- CDP approval (M144+): `chrome://inspect/#remote-debugging`; user approves each
  connection. `--remote-debugging-port`/`-pipe` are refused on the default
  user-data dir only in Google-branded builds. This exposes
  `Page.getAnnotatedPageContent` and the `WebMCP` domain with **none of rac's
  guard**. INFERENCE.
- WebMCP is the reverse direction. `readOnlyHint`, `untrustedContentHint`, and
  `consequentialHint` are page-authored; Google says the browser *can* ask, not
  that it will. Browser-side permission-policy enforcement landed in `cff8d8f`
  (2026-09-25, M156); **154 lacks it**.
- Built-in AI APIs are web-exposed on Mac in 154: Prompt (`LanguageModel`),
  Summarizer, Translator, Language Detector stable; Writer, Rewriter,
  Proofreader trial/experimental. **None run in rac**: ungoogled sets
  `use_on_device_model_service=false`, the library is closed, and Helium's
  component allowlist blocks models. `availability()` inferred "unavailable".
  Gemini Nano needs ≥22 GB free plus >4 GB VRAM or 16 GB RAM and 4 cores, in
  Google Chrome only
  ([Chrome for Developers](https://developer.chrome.com/docs/ai/get-started)).

### Build, CI, release

- GN + siso; features behind `base::Feature` with Finch parameters. Finch does
  **not** reach rac: Bromite's `disable-fetching-field-trials.patch`
  (`R:helium-chromium/patches/series:38`) stops seed fetching, and
  `disable_fieldtrial_testing_config=true` drops the in-tree config. A
  Finch-only launch stays at its source default.
- Tests are heavy: Glic has 16 `interactive_uitest` files plus 2 shared helpers;
  the actor has more test than product code. Actor and APC opted into Chromium
  AI Code Review in October 2026; the repo ships an agent skill for registering
  tools.
- Chrome releases on the two-week train and removes kill switches after launch
  (`kGlicActionUseOptimizationGuide` 2026-10-23, `kGlicEarlyAddTaskTabs`
  2026-10-15). rac tracks via quilt; the Helium dossier counts 59 of 180 rac
  patches failing on 0.20.1.1, mostly UI.

## What rac should take (ranked)

Costs: **S** ≤3 days, **M** 1–2 weeks, **L** ≥3 weeks. All INFERENCE.

1. **Ask before the first new-site visit at `auto` (S).** One card on the first
   navigation or cross-site link to an origin outside the task's named set, then
   treat it as named for the turn. Typing model-written text asks on any site
   the *user* did not name. Chrome made the same default on 2026-10-19
   (`8799124`); its motive is unstated, so "same reason" is INFERENCE. Change
   `ActionGuard`'s level table; extend `AutoAsksOnlyForRiskAndForeignTyping`.
2. **Pin-and-dry-run harness before the Helium sync (S).** A script like
   `/tmp/rac-overhaul/scripts/dry.sh`, plus a compile/`static_assert` test
   pinning `ScrollAction`, `AIPageContentResultOrError`, and `InvokeTool`.
   Pre-port the two M158 breaks behind `#if CHROME_VERSION_MAJOR >= 158`, or fix
   them in the 158 sync.
3. **Keep Chromium AI symbols behind two rac files (S–M).** `renderer_tools` and
   `apc_extract` already hold 47 of 91 uses. Move `snapshot_serializer`'s proto
   reads and `link_fetcher`/`page_context` result handling behind them.
4. **Read-only origin set for page content (M).** Leave cross-origin iframe
   content outside the task's set out of snapshots and page text, or show a
   labelled stub. APC exposes each frame's origin.
5. **WebMCP page tools after syncing to ≥156 (M).** Needed for `cff8d8f`. List
   `script_tools` as untrusted snapshot lines, e.g.
   `- page tool "add_to_cart" [ref=t3] (consequential)`. Add `call_page_tool`
   sending `ToolAction::NewScriptTool` over `InvokeTool`. Treat every page tool
   like a click on a named site; `consequentialHint` or missing `readOnlyHint`
   makes it risky. Wrap output in the page-text nonce; expose the same tools to
   outside agents via rac's MCP. Optionally override the feature so trial tokens
   are not needed.
6. **Real-page snapshot tests (M).** Save ~30 pages as MHTML, run the real APC
   extractor, diff serialized snapshots per sync. Catches label sources,
   checkbox/radio `field_value` removal, MathML, unknown ARIA roles, and
   `<summary>` becoming a button.
7. **Ship a local sensitive-site list (S–M).** Curated banks, health,
   government, payments, email, built in with no network. Make "first action on
   this site" a risky card at every level. Add `--rac-agent-sensitive-sites=`
   for tests, modeled on `--actor-sensitive-sites`. The list is the work.
8. **Trace every turn for evals and red-teaming (M).** Record tool calls, guard
   decisions, page hashes, and card answers to local JSON or Perfetto behind a
   switch, modeled on `--actor-trace-path`/`parse_actor_trace.py`. Replay
   injection pages in CI.
9. **Secret-free login, later (L).** Model asks to sign in; rac shows a
   credential picker; browser fills; the model never sees the password. Only if
   it works on `password_manager` without `ExecutionEngine` — **open**.
10. **A calm acting cursor (S–M, Opus/UI).** Static target marker, a move of
    ≤300 ms at `cubic-bezier(0.6,0,0.4,1)`, and a 400 ms press. No glow, idle
    loop, or infinite animation; all off under reduced motion.
11. **Use Chrome's tool names in rac's MCP (S).** At least `navigate`, `click`,
    `type`, `switch_tab`, `open_url`, `scroll`, `select_option`, `go_back`.
    Outside agents trained on Chrome's catalog will guess right.
12. **Document CDP approval as advanced, not default (S).** Works with AI off and
    costs nothing then, but bypasses rac's guard. Verify
    `chrome://inspect/#remote-debugging` in rac and record `DevToolsActivePort`
    under rac's profile.

## What rac should avoid

- **`ExecutionEngine`, `ActorKeyedService`, Glic, or the browser actuator.**
  Safe Browsing off blocks nearly every action; the only bypass,
  `--disable-actor-safety-checks`, disables every other check too. Lists and
  models come from Google; the layer churns daily.
- **Reviving Gemini Nano or the built-in AI web APIs.** Closed library, service
  not built, components blocked, Google's model license.
- **Backing the web Prompt API with the user's key or local model.** Every site
  would spend the user's key/compute, availability would fingerprint the user,
  and it conflicts with "AI off costs nothing".
- **Turning on PCES automatic extraction.** It extracts every page on load.
- **Disabling `kGlicActor` to save idle objects.** The renderer `CHECK`s it.
- **Relying on optimization-guide sensitive-site hints.** They fail open in
  Helium.
- **Trusting WebMCP descriptions/annotations, or using WebMCP on 154.** No
  browser-side policy check until M156.
- **Copying the ever-pulsing glow, the reduced-motion-ignoring spinner, or the
  seven-surface status UI.** Seven surfaces (glow, cursor, spinner, icon,
  bubble, toast, notification) are noisy beside rac's single ring and pill.

## Caveats

- **No build was run.** The dry run compares patch text only; real migration to
  156/158 needs a worktree build and maintainer approval.
- **Unmeasured:** idle cost of the actor objects with AI off.
- **WebMCP ship date unresolved.** Third parties say Chrome 157 enables it
  (CLAIM); U157/UM source still says `experimental`; chromestatus lists no ship
  milestone. A Finch launch would not reach rac anyway.
- **Not run in rac:** CDP approval mode and `DevToolsActivePort` location;
  `LanguageModel` exposure and `availability()` (INFERENCE: unavailable).
- **Not traced:** whether `ActorLoginService`/autofill works without
  `ExecutionEngine`.
- Google's server-side planner, critic, classifier, red-team suite, and
  sensitive-site list cannot be inspected; safety claims are Google's (CLAIM).
- As of HL `f29a259`, Helium prunes only WebUI resources and Skills; actor
  renderer code is intact. Later pruning is unknown.
- Commit counts are GitHub path-filtered; renames can skew them.
- Verification checked 40 claims and corrected 11 (rows 9, 10, 11, 17, 18, 23,
  24, 27, 28, 33, 39), all applied. Confidence is **high** for architecture,
  gating, and API breaks; **medium** for counts, dates, and labels.

## Where to look in the full dossier

`plans/research/chromium-agent-internals.md` (791 lines). Plain English 29–39;
snapshot, versions, team, size, churn 41–56; features 58–159; UI and exact motion
161–202; process model 204–281; storage and idle cost 283–307; agent mechanics,
tools, permissions, CDP, WebMCP 309–401; rac's patches, API table, dry run, risk
403–492; built-in AI 494–501; build/CI/release 503–523; strengths/weaknesses
525–553; ranked take/avoid 555–643; open questions 644–667; sources 669–724;
verification log 726–791.
