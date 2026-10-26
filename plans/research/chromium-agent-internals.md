# Chromium's built-in agent stack (actor, Glic, APC, WebMCP, built-in AI): research dossier

Researched 2026-10-25. Subject: the agent code inside Chromium. That means the `actor`
framework, which plans and runs browser actions; Glic, which is "Gemini in Chrome"; and
`optimization_guide` Annotated Page Content (APC), which turns a page into a structured tree.
It also covers origin gating, WebMCP (tools that a web page publishes for agents), and the
built-in AI web APIs. The dossier ends with exactly what rac's `patches/rac/agent/` uses, and
how risky that is.

Citation shorthand:

- **C:** the read-only rac build tree `/Users/knewton/Dev/Github/rac/build/src`
  (Chromium 154.0.8037.92 with Helium 0.18.2.1 and rac patches applied, `chrome/VERSION`).
- **U156 / U157 / UM:** `chromium/chromium` on GitHub at tag `156.0.8078.48` (current
  Stable), tag `157.0.8103.15` (current Beta), and `main` at `edd1071` (main position
  1726612, 2026-10-25, the 158.0.8124.0 Canary). `main` has since moved (`c9ed90a`,
  position 1726660, 2026-10-25T20:10Z); the verifier re-checked against `edd1071`. Release data comes from
  `chromiumdash.appspot.com/fetch_releases` and `fetch_milestones`.
- **R:** this rac worktree at `cfdcf83`.
- **H:** Helium core as vendored in rac (`R:helium-chromium/`, 0.18.2.1).
- **HL:** the latest Helium core clone at `/tmp/rac-overhaul/src/helium` (`f29a259`, 2026-10-21).
- **Commit counts** come from `gh api repos/chromium/chromium/commits?path=…` on `main`
  since the 154 branch point (main position 1689415, `e10b20e`, 2026-08-31T23:52Z). Raw
  lists are in `/tmp/rac-overhaul/work/commits_*.tsv`.

Tags: **FACT** = primary source (code, official doc). **CLAIM** = vendor marketing or
third-party report. **INFERENCE** = my reasoning.

## In plain English

Chrome has a built-in toolkit for AI agents. Google uses it for "auto browse", where Gemini
clicks and types on websites for you. The toolkit has three layers. The first turns a page
into a tidy outline that a model can read. The second clicks, types, and scrolls inside the
page. The top layer, Glic, is the Gemini panel. It needs Google's servers and a Google account.
rac uses the bottom two layers and skips Glic. That was the right choice. Chrome's own task
engine refuses to act when Google's malware-site check is off, and Helium always has it off.
Google changes this code about seven times a day, but mostly in the parts rac skips. Chrome's
on-device AI (Gemini Nano) cannot run in rac at all. Websites can now publish tools for
agents to use (WebMCP). rac could add support for that cheaply.

## Snapshot

| Field | Value |
| --- | --- |
| What it is | Google's agent framework inside Chromium. **actor:** tasks, a tool engine, and page tools that run in the renderer (`C:chrome/browser/actor`, `C:chrome/renderer/actor`, `C:components/actor`). **Glic:** the host for the Gemini web client (`C:chrome/browser/glic`). **APC:** structured page extraction (`C:third_party/blink/renderer/modules/content_extraction`, `C:components/optimization_guide/content/browser`). **Origin gating:** which sites an agent may visit or act on (`C:components/origin_gating`). **WebMCP:** `document.modelContext` (`C:third_party/blink/renderer/core/script_tools`). **Built-in AI:** `LanguageModel`, `Summarizer`, and the others (`C:chrome/browser/ai`, `C:services/on_device_model`). FACT |
| Engine | Chromium/Blink. rac reads it at 154.0.8037.92. Stable is 156.0.8078.48, Beta 157.0.8103.15, Canary 158.0.8124.0 (chromiumdash, 2026-10-25). FACT |
| Platforms | The actor runs on desktop and on Android, where some tools are still unported (`SKIP_ANDROID_UNMIGRATED_ACTOR_FILES`, `C:chrome/browser/actor/tool_request_variant.h:15-53`). `kGlic` is on by default on Mac, Windows, ChromeOS, and Android (`C:chrome/common/chrome_features.cc:588-595`). The auto browse product is limited to US Google AI Pro and Ultra subscribers ([9to5Google, 2026-01-28](https://9to5google.com/2026/01/28/chrome-gemini-auto-browse/)). FACT / CLAIM |
| License | The client code is BSD-3-Clause, under Chromium. The model, the planner, the critic, and the prompt-injection classifier all run on Google's servers and are proprietary ([Google, 2025-12-08](https://blog.google/security/architecting-security-for-agentic/)). The on-device inference library `optimization_guide_internal` is closed (`C:services/on_device_model/ml/chrome_ml_holder.cc:25`, `C:components/optimization_guide/features.gni:41-45`). FACT |
| Repo | chromium.googlesource.com/chromium/src. The GitHub mirror is `chromium/chromium`. FACT |
| Stars | 25,138 on the read-only GitHub mirror (`gh api repos/chromium/chromium`). This number is not meaningful for a mirror. FACT |
| Age | Glic code existed by 2024-11-27 (a mirror commit touching `chrome/browser/glic` has that date; I did not search earlier). The first `chrome/browser/actor` commit is 2025-03-17, "Add coordinator to handle glic actions". FACT |
| Release cadence | Chrome branches every two weeks from M153 on. Branch points: 153 on 2026-08-18, 154 on 08-31, 155 on 09-14, 156 on 09-29, 157 on 10-13. Before that the gap was longer (152 on 07-27, 151 on 06-29). FACT (chromiumdash `fetch_milestones` branch hashes, dated with `gh api`) |
| Team size | Unique commit authors since 2026-08-31: 87 in `chrome/browser/actor`, 162 in `chrome/browser/glic`, and 26 in `components/actor`. `C:chrome/browser/actor/OWNERS` lists 13 owners. `C:chrome/browser/glic/OWNERS` includes `file://components/glic/OWNERS`, which lists 8, plus per-file owners. FACT |
| Business model | Gemini subscriptions. Auto browse is gated to AI Pro and Ultra. Third-party reports put the price at $19.99 and $249.99 a month, with caps of 20 and 200 tasks a day ([aiagentslibrary](https://www.aiagentslibrary.com/blog/gemini-spark-chrome-auto-browse/)). CLAIM |
| Code size (154, non-test / test lines) | Verifier recount, `.cc` and `.h` only, "test" = filename contains `test`: `chrome/browser/actor` 32,510 / 40,253. `chrome/renderer/actor` 5,823 / 121. `components/actor` 3,009 / 1,124. `chrome/browser/glic` 75,535 / 74,131. APC in Blink 6,052 / 11,112. APC in the browser 6,032 / 9,947. WebMCP in Blink 1,676 / 2,037. `chrome/browser/ai` 7,211 / 8,784. `services/on_device_model` 9,362 / 2,872. FACT (`wc -l`). The original figures used an unstated method and differed by up to 40% for `components/actor`; the shape (actor has more test lines than code) holds either way |
| Churn since the 154 branch (55 days) | 405 commits in `chrome/browser/actor`, 756 in `chrome/browser/glic`, 53 in `components/actor`, 27 in WebMCP (`core/script_tools`), 19 in Blink APC, 11 in `chrome/renderer/actor`, and 2 in `chrome/common/actor.mojom`. FACT |

## Features

Status key: **shipped** means on in Chrome Stable. **flag** means it ships but is off by
default, or sits behind a trial. **planned** means it is in development on `main`. The
"rac?" column says whether the feature works in rac's Helium-based build today.

### Tabs, sidebar, spaces

| Feature | Status | rac? | Evidence |
| --- | --- | --- | --- |
| Gemini panel, docked in the side panel or detached as a floating window, with several instances | shipped | no | `AttachPanel`/`DetachPanel` (`C:chrome/browser/glic/host/glic.mojom:1203-1207`). `kGlicMultiInstance` is on (`C:chrome/common/chrome_features.cc:624`). FACT |
| Share chosen tabs with Gemini (the "pin tabs" context, with a tab picker) | shipped | no | `PinTabs`, `SetMaximumNumberOfPinnedTabs`, `OpenPinnedTabPicker` (`glic.mojom:1248-1271`). FACT |
| Agent task icon in the tab strip, a task list bubble, and nudges ("Working on your task…", "Waiting for your help") | shipped | no | `C:chrome/app/actor_strings.grdp`, `C:chrome/browser/actor/ui/task_list_bubble/`. FACT |
| Spinner on tabs the agent is working in | shipped | objects only | `kGlicActorUiTabIndicator` (`chrome_features.cc:407-409`). Each tab still builds `ActorUiTabController` (`C:chrome/browser/ui/tabs/tab_features.cc:421-430`). FACT |
| Spaces, folders, pinned-tab model | absent | n/a | Nothing in the stack. FACT |

### Navigation and command bar

| Feature | Status | rac? | Evidence |
| --- | --- | --- | --- |
| AI Mode in the omnibox, plus a policy for third-party AI Mode | shipped (Google) | no | `C:components/policy/resources/templates/policy_definitions/GenerativeAI/ThirdPartyAiChatSettings.yaml`. FACT |
| `navigate`, `go_back`, `go_forward`, `reload_page` tools | shipped | rac has its own versions | `ToolId` enum (`UM:chrome/browser/actor/tools/registry/tool_definition.h`). FACT |
| `open_url` (current or new tab), `switch_tab` (match a query against tab titles and URLs), `perform_search`, site-based search, `open_known_page` (settings pages) | in code from M156 to M158 | no | `switch_tab_tool_request.cc` and `perform_search_tool_request.cc` already exist at U156. `open_known_page_tool_request.cc` first appears at U157. `open_url_tool_request.cc` exists only on main (commit `3cc2ba10`, 2026-10-23). Checked with `gh api …/contents?ref=<tag>`. FACT |
| Zero-state suggestions for the focused tab | shipped | no | `GetZeroStateSuggestionsForFocusedTab` (`glic.mojom:1430`). FACT |

### Split view, peek, small windows

| Feature | Status | rac? | Evidence |
| --- | --- | --- | --- |
| Floating Gemini window | shipped | no | `glic.mojom:1203-1207`. FACT |
| Open a link in a popup at a size Gemini chooses | shipped | no | `OpenLinkInPopup(url, w, h)` (`glic.mojom:1184`). FACT |
| Picture-in-picture of a running task, and background actuation | shipped on Android and tablets | no | Commits 2026-09-25 and 09-26, "Enable Picture-in-Picture and Background Actuation for Tablets". `kGlicBackgroundActuation` is off on desktop (`chrome_features.cc:597`). FACT |
| Headless "actor surfaces": the agent acts in WebContents with no tab | planned (M156 to M158) | no | "Add ActorSurface abstraction for tab and headless actuation" (`31cd13c8`, 2026-09-28T20:30Z, hours before the M156 branch). "Add HeadlessWebContentsManager" (`27a6b536`, 2026-09-29, M157). FACT |

### Import, sync, profiles

| Feature | Status | rac? | Evidence |
| --- | --- | --- | --- |
| Agent limited to regular profiles | shipped | rac has the same rule | `ProfileSelections::BuildForRegularProfile()` (`C:chrome/browser/actor/actor_keyed_service_factory.cc:33`). FACT |
| Skills: named, saved prompts that Gemini can run; enterprise-published skills | shipped | no; `disable-ai.patch` removes them | `struct Skill` (`glic.mojom:626-634`). `EnterprisePublishedSkills.yaml`. `H:patches/ungoogled-chromium/disable-ai.patch` (skills hunks). FACT |
| Import of other browsers' data | absent | n/a | FACT |

### Privacy and blocking (the agent's safety layers)

| Feature | Status | rac? | Evidence |
| --- | --- | --- | --- |
| Origin gating: an ordered list of 19 predicates over three event types (navigation request, navigation response, page action) | shipped | not used | `C:chrome/browser/actor/execution_engine.cc:683-760`. FACT |
| Blocks navigation requests and page actions when Safe Browsing is off | shipped | **would block almost everything**: rac builds with `safe_browsing_mode=0` | `BlockIfSafeBrowsingDisabled` (`execution_engine.cc:423-437`) is predicate 9 of 19 and covers navigation requests and page actions. Three earlier predicates can still decide first: about:blank is allowed, localhost navigation requests are allowed, and the `--disable-actor-safety-checks` switch allows everything (`AllowIfSafetyChecksDisabled`, `C:components/actor/core/actor_util.cc:14-17`). `safe_browsing_mode=0` is in both the dev tree (`C:out/Default/args.gn:14`) and release flags (`R:helium-chromium/flags.gn:14`), which sets `SAFE_BROWSING_AVAILABLE=false` (`C:components/safe_browsing/BUILD.gn:27-29`). FACT |
| Sensitive-site check against a list Google serves (`GLIC_ACTION_PAGE_BLOCK` hints). Fails open when the hints component is missing | shipped | no list ever arrives | `C:chrome/browser/actor/site_policy.cc:39-78`. Helium allows only two components, CRLSet and Widevine (`H:patches/helium/core/component-updates.patch:144-158`). FACT |
| `--actor-sensitive-sites=` switch: a local list of sensitive sites | shipped (M155) | not in 154 | `UM:components/actor/core/actor_switches.cc`. Commit 2026-09-18. FACT |
| Confirm before navigating to a new origin | flag in 154; **on by default from M158** (2026-10-19) | rac has its own rules | `kGlicConfirmNavigationToNewOrigins` defaults to false (`C:components/actor/core/actor_features.cc:38-41`). Commit `8799124` "Flips the default value… to true". FACT |
| Sensitive-site confirmations cached per site, not per origin | planned (M158) | n/a | Commit `a84713b` (venmo.com and auth.venmo.com example). FACT |
| Lookalike-domain block; localhost treated as sensitive; non-localhost IP addresses blocked; dangerous MIME types blocked; File System Access picker blocked | shipped | rac blocks pickers and IPs its own way | `execution_engine.cc:314-421`, `actor_features.cc:21-29`. FACT |
| Static allow and block lists (JSON `from`→`to` URL patterns) delivered by the component updater | shipped | never downloaded | `C:components/actor/core/safety_list_manager.h:20-75`, `C:components/component_updater/installer_policies/actor_safety_lists_component_installer.cc`. FACT |
| Time-of-use check: the renderer re-checks that the target is still the node the model saw | **off by default** | **rac turns it on** | `kGlicActorToctouValidation` is DISABLED in upstream 154 and still DISABLED at `UM:chrome/common/chrome_features.cc:499`. rac's tree shows rac's flip at `C:chrome/common/chrome_features.cc:536-537`. rac flips it (`R:patches/rac/agent/03-actions.patch:2139-2148`). The check itself is at `C:chrome/renderer/actor/tool_base.cc:636-750`. FACT |
| Redaction of password, payment, and one-time-code fields in APC and screenshots; redaction of cross-site iframes in screenshots | shipped | APC redaction applies to rac | `C:third_party/blink/public/mojom/content_extraction/ai_page_content.mojom:524-540,726-747`. `kScreenshotIframeRedaction` defaults to `kCrossSite` (`actor_features.cc:115-131`). FACT |
| Login without the model seeing the password: the user picks a saved credential and the browser fills it | shipped | no | `C:chrome/browser/actor/tools/attempt_login_tool.cc:160-233`, `C:components/password_manager/core/browser/actor_login/`. FACT |
| Enterprise policies: `GeminiActOnWebSettings`, `GeminiActOnWebAllowedForURLs` and `…BlockedForURLs`, `GeminiSettings`, `GenAILocalFoundationalModelSettings` | shipped (Chrome 143+ for act-on-web) | n/a | `C:components/policy/resources/templates/policy_definitions/GenerativeAI/*.yaml`. FACT |
| Per-task policy (`ActorContainerConfig`, renamed `TaskPolicyConfig`): location rules with "may use the user's session" as a resource | planned | no | `C:components/origin_gating/core/actor_container_config.h:24-120`. Commit `c34b574` makes it "almost-purely restrictive". FACT |

### AI assistant

| Feature | Status | rac? | Evidence |
| --- | --- | --- | --- |
| Gemini in Chrome: chat about a page, sending its inner text, APC, a viewport screenshot, or PDF bytes | shipped | no | `TabContextOptions` (`glic.mojom:387-417`). FACT |
| Gemini Live (microphone), region capture, image sharing | shipped or flag | no | `glic.mojom:1213,1287-1306`. `kGlicShareImage` is off (`chrome_features.cc:1069`). FACT |
| Built-in AI web APIs: Prompt (`LanguageModel`), Summarizer, Writer, Rewriter, Proofreader, Translator, Language Detector | Prompt, Summarizer, Translator, and Language Detector are "stable" on Mac in this tree; Writer and Rewriter are "experimental" with origin trials; Proofreader is an origin trial | **No.** The JS API exists, but no model can run | `AIPromptAPI` is stable on Mac (`C:third_party/blink/renderer/platform/runtime_enabled_features.json5:406-415`). ungoogled sets `use_on_device_model_service = false` (`H:patches/ungoogled-chromium/fix-building-with-prunned-binaries.patch:107-108`). FACT. That availability then reports "unavailable" is INFERENCE |

### Agent

| Feature | Status | rac? | Evidence |
| --- | --- | --- | --- |
| Task model: `ActorTask` with states Created, Acting, Reflecting, PausedByActor, PausedByUser, WaitingOnUser, Cancelled, Finished, Failed; stop reasons | shipped | rac has its own turn model | `C:chrome/browser/actor/actor_task.h:140-188`. FACT |
| 25 action types in the `Actions` proto that the server sends | shipped | rac uses 4 renderer actions | `C:components/optimization_guide/proto/features/actions_data.proto:483-535`. FACT |
| Tool registry: model-facing names plus a JSON Schema per tool | in code from M157 (23 tool IDs at U157), 40 tool IDs at UM `edd1071` | no | `UM:chrome/browser/actor/tools/registry/README.md`, `tool_definition.h:19-101` (`kNavigate = 0` … `kOpenUrl = 39`, `kMaxValue = kOpenUrl`). FACT |
| Take over, pause, interrupt, resume; "Leave site and end task?" | shipped | rac has pause, resume, and Stop | `actor_task.h:212-235`, `actor_strings.grdp`. FACT |
| Journal of every step; optional trace file (`--actor-trace-path`); `chrome://actor-internals` | shipped | the journal is used in the renderer; Helium removed the internals page in 0.19.3.1 | `C:chrome/browser/actor/actor_keyed_service.cc:151-185`. `HL:patches/helium/core/remove-unused-ai-resources.patch`. FACT |
| User Alignment Critic, prompt-injection classifier, automated red teaming | shipped, server side | n/a | [Google, 2025-12-08](https://blog.google/security/architecting-security-for-agentic/). CLAIM |
| Tasks the server starts ("experimental triggering", Gemini Spark) | flag | no | `kGlicExperimentalTriggering` is off (`chrome_features.cc:281-301`). FACT |
| Browser actuator: Google's server pushes actions over a long-lived HTTPS stream | planned (since 2026-07-08) | no | `UM:components/browser_actuator/README.md`, `…/internal/transport/README.md`. FACT |

### Extensibility (CLI, MCP, API, extensions)

| Feature | Status | rac? | Evidence |
| --- | --- | --- | --- |
| WebMCP, imperative: `document.modelContext.registerTool/getTools/executeTool`, with `readOnlyHint`, `untrustedContentHint`, and `consequentialHint` | origin trial in Chrome 149–156 (FACT: chromestatus feature 5117755740913664, origin-trial stage desktop 149 to 156; its ship stage has no milestone); still "experimental" in U157 and UM source | Works on pages that serve a trial token, or with a feature override. rac's agent ignores these tools | `C:third_party/blink/renderer/core/script_tools/model_context.idl`, `model_context_tool.idl`. The flag is at `runtime_enabled_features.json5:7026-7039`; `status: "experimental"` at both U157 and UM. FACT |
| WebMCP, declarative: `<form toolname tooldescription>` | same | same | `C:third_party/blink/renderer/core/html/forms/html_form_element.cc:351-365`. FACT |
| WebMCP tools inside APC: each frame lists its `script_tools` | shipped | **rac's APC already carries them and drops them** | `ai_page_content.mojom:439`. No `script_tool` use in `R:patches/rac/` (grep). FACT |
| Actor can call a page's WebMCP tool (`ScriptToolAction`) | shipped | the same `InvokeTool` path rac already uses | `C:chrome/common/actor.mojom:135-150`, `C:chrome/renderer/actor/script_tool.cc:108-112`. FACT |
| CDP `Page.getAnnotatedPageContent` | experimental, shipped | yes, when remote debugging is on | `C:third_party/blink/public/devtools_protocol/domains/Page.pdl:1785-1795`. FACT |
| CDP `WebMCP` domain: list page tools, invoke them, get tool events | experimental, shipped | same | `C:third_party/blink/public/devtools_protocol/domains/WebMCP.pdl`. FACT |
| Remote debugging the user approves per connection (`chrome://inspect/#remote-debugging`, M144+) | shipped | likely, not run | `C:chrome/browser/devtools/remote_debugging_server.cc:185-247`. `chrome-devtools-mcp --autoConnect` (`/tmp/rac-overhaul/src/chrome-devtools-mcp/docs/advanced-usage.md:55-101`). FACT (code); INFERENCE (works in rac) |
| Chrome extensions read and run WebMCP tools through content scripts | shipped | yes | [developer.chrome.com WebMCP tool security](https://developer.chrome.com/docs/ai/webmcp/secure-tools). FACT |
| An agent "skill" in the Chromium repo that teaches coding agents to register tools | meta | n/a | `UM:chrome/browser/actor/tools/registry/README.md` ("actor-tool-registration"). FACT |

### Other

| Feature | Status | rac? | Evidence |
| --- | --- | --- | --- |
| Automatic APC extraction on page load, with an in-memory and SQLite cache (PCES) | flag (`kAnnotatedPageContentExtraction` off) | rac uses the direct call instead | `C:components/page_content_annotations/core/page_content_annotations_features.cc:111-112`, `C:components/page_content_annotations/content/pces_guide.md`. FACT |
| "Structured Markdown" and "passage chunk" views of APC | mentioned in the readme | no converter in Chromium | `C:…/content_extraction/readme.md` §4. No markdown code in `components/optimization_guide/content` or `components/page_content_annotations` (grep). INFERENCE: these views are built on Google's servers |
| Gemini Nano on-device model (needs at least 22 GB free on the profile's volume, plus more than 4 GB of VRAM, or 16 GB of RAM and 4 cores) | shipped in Google Chrome only | no | `C:chrome/browser/component_updater/optimization_guide_on_device_model_installer.cc:54` (`OptGuideOnDeviceModel`). Hardware needs per [Chrome for Developers, "Get started with built-in AI"](https://developer.chrome.com/docs/ai/get-started). FACT |

## UI, look, and feel

Chrome's agent UI is spread over about seven surfaces. There is a WebUI overlay on the page
with a "magic cursor" and a border glow. There is a tab-strip task icon with a bubble, a tab
spinner, toasts, a "handoff" (take over) button, desktop notifications, and an alert dialog
when the user leaves a site (`C:chrome/browser/actor/ui/`, `C:chrome/app/actor_strings.grdp`).
Sub-flags switch each surface on or off (`C:chrome/common/chrome_features.cc:387-412`). FACT

**Motion, taken from code:**

| Element | Parameters | Evidence |
| --- | --- | --- |
| Border glow inside the acted-on page | `box-shadow: inset 0 0 35px 12px #4C8DF6`. Opacity pulses 0.6 → 0 → 0 → 0.6 over **4000 ms, infinite**, using `cubic-bezier(0.33,0,0.67,1)` with a linear hold. **No reduced-motion guard.** | `C:chrome/browser/resources/actor_overlay/app.css:24-40,64-72`. FACT |
| Magic cursor movement | 24 px SVG with two blue drop shadows. Moves at 1.5 px/ms, clamped to 50–300 ms per move, with `transition-timing-function: cubic-bezier(0.6,0,0.4,1)`. With reduced motion, a move takes 0 ms | `app.css:74-98`. `chrome_features.cc:370-379`. `C:chrome/browser/resources/actor_overlay/app.ts:244-279`. FACT |
| Cursor "click" | 400 ms `ease-out`. At 40% it is `scale(0.85) translateY(2px)` | `app.css:156-171`. FACT |
| Cursor "thinking" | A 750 ms intro, then a 3200 ms infinite loop (750 ms per 4 px with 100 ms holds). Turned off under reduced motion | `app.css:107-154`. FACT |
| Cursor fade | 200 ms `ease` | `app.css:97`. FACT |
| Glic context-sharing border | Ramps up in 500 ms, holds 1500 ms, ramps down in 1000 ms (EASE_OUT, then EASE_IN_OUT_2). Corner radius 12 | `C:chrome/browser/glic/browser_ui/context_sharing_border_view.cc:26-34,267-271`. FACT |
| Glic animated effect (a shader glow) | Opacity in 500 ms, out in 200 ms. Under reduced motion (or a forced simple shader) it skips the animation cycle, holds the effect still, and fades in over 200 ms instead | `C:chrome/browser/glic/browser_ui/animated_effect_view.cc:34-41,251-253,345-347,402-418`. FACT |
| Glic selection widget | 250 ms fade in, 250 ms bounds change, `FAST_OUT_SLOW_IN` | `C:chrome/browser/glic/browser_ui/glic_selection_widget.cc:88,105,742`. FACT |
| Tab underline for shared tabs | 3000 ms cycle | `C:chrome/browser/glic/browser_ui/tab_underline_view.cc:29`. FACT |
| UI debounce | 25 ms for hover events on the overlay and handoff button, 500 ms for profile-wide UI updates. A finished task stays listed for 30 s | `chrome_features.cc:416-420`. `C:chrome/browser/actor/ui/actor_ui_state_manager_interface.h:19-20`. FACT |

**What feels good.** The cursor travels to the target before a click. A user can see where
the agent is about to act, and the 300 ms cap keeps that from slowing the agent down. The
words are plain: "Working on your task…", "Waiting for your help", "Paused", "Done". A
"take over" button hands control back in one step. INFERENCE (from code and strings)

**What feels bad.**

- The border glow animates forever, on a 4 s loop, and ignores reduced motion. It animates
  only opacity, which the compositor can usually run without a main-thread repaint, but it
  still produces frames for as long as a task runs. That breaks the spirit of rac's
  "nothing that repaints continuously" rule. FACT (code); INFERENCE (judgment and cost)
- `kGlicActorUiTabIndicatorSpinnerIgnoreReducedMotion` is on by default. Chrome
  deliberately ignores the user's reduced-motion setting for the tab spinner
  (`chrome_features.cc:324-328`). FACT
- While a task runs, the overlay blocks input to the page: "To interact with this site,
  pause the current task or wait for Gemini to finish working" (`actor_strings.grdp`).
  rac instead pauses on real input, which is calmer. FACT / INFERENCE
- Seven surfaces at once (glow, cursor, spinner, icon, bubble, toast, notification) is noisy
  next to rac's single ring and pill. INFERENCE

## Architecture

### Process model

```
Google servers (Gemini planner, critic, injection classifier)        <- closed
      ^  APC proto + screenshot + inner text      |  Actions proto (25 kinds)
      |                                           v
chrome://glic WebUI -> <webview> gemini.google.com/glic  --glic.mojom ActorHandler-->
Browser process:  ActorKeyedService (1/profile) -> ActorTask (N) -> ExecutionEngine
                     -> origin gating (19 predicates) -> ToolController -> Tool (browser side)
                     -> ObservationDelayController / page stability -> TabObservation
Renderer process: ChromeRenderFrame::InvokeTool -> ToolExecutor -> ToolBase subclass
                     (click, type, scroll, select, drag, move, scroll_to, script_tool)
                  AIPageContentAgent (walks the layout tree) -> blink.mojom.AIPageContent
                  ModelContext (WebMCP) <-> content::ModelContextUserData
Utility process:  On-Device Model Service -> closed optimization_guide_internal library
```

- **Glic** is a WebUI that hosts a guest `<webview>` of `https://gemini.google.com/glic`
  (`kGlicGuestURL`, `C:chrome/common/chrome_features.cc:689-691`). It talks to the browser
  over `glic.mojom`, a 2,391-line interface (`C:chrome/browser/glic/host/glic.mojom`). The
  agent part is `ActorHandler` (`glic.mojom:893-1015`). Its key call is
  `PerformActions(array<uint8> actions_proto)` (`:930`). So **the model never runs in the
  browser**. The browser only executes protos and returns observations. FACT
- **Glic needs a signed-in Google account** (`C:chrome/browser/glic/public/glic_enabling.cc:442`).
  ungoogled-chromium has no Google sign-in, and its domain substitution rewrites
  `chrome_features.cc`, which holds the Gemini URL
  (`R:helium-chromium/domain_substitution.list:2406`). Helium also strips the Glic entry
  points from the context menu (`H:patches/helium/core/degoogle-context-menu.patch:46-64`).
  FACT. Domain substitution runs in release builds (`R:devutils/shared.sh:38`); the dev tree
  at C: is unsubstituted, so it still shows `gemini.google.com`. Glic is compiled into rac but
  unreachable. INFERENCE
- **The tool engine** (`ExecutionEngine`) runs a state machine: Init → StartAction →
  CreateAndVerify → UiPreInvoke → ToolInvoke → UiPostInvoke → Complete
  (`C:chrome/browser/actor/execution_engine.cc:803-815`). Browser-side tools
  (navigate, tabs, windows, history, login, autofill, media, translate) run in the browser.
  Page tools cross into the renderer through `ChromeRenderFrame::InvokeTool`
  (`C:chrome/renderer/chrome_render_frame_observer.cc:685-699`). FACT
- **The renderer tool executor CHECKs `kGlicActor`**
  (`C:chrome/renderer/actor/tool_executor.cc:45`; still at `UM:…/tool_executor.cc:44`).
  Turning off Chromium's actor feature would therefore crash rac's agent. FACT
- **APC** is built by walking Blink's *layout* tree, not the DOM, so only rendered content
  appears (`C:third_party/blink/renderer/modules/content_extraction/readme.md` §3). The
  browser gets it through `optimization_guide::GetAIPageContent(web_contents, options, cb)`
  (`C:components/optimization_guide/content/browser/page_content_proto_provider.h:144-146`).
  There are two modes: `kDefault` and `kActionableElements`, which adds geometry, z-order,
  and interactivity (`ai_page_content.mojom:680-690`). Options include `on_critical_path`,
  `include_same_site_only`, `node_id_allowlist`, an ad filter, and password, payment, and OTP
  redaction boxes (`:698-748`). FACT
- **WebMCP**: Blink's `ModelContext` registers each tool with the browser through
  `ModelContextHost.RegisterScriptTool`. Tools are same-origin by default; `exposedTo` lists
  other origins (`C:third_party/blink/public/mojom/content_extraction/script_tools.mojom:52-120`).
  The actor runs a tool through `ScriptToolAction{name, input_arguments}` on the normal
  `InvokeTool` path (`C:chrome/common/actor.mojom:135-150`). FACT
- **The browser actuator** (on main since 2026-07) is a new layered component. Google's
  OnePlatform endpoint keeps a never-ending HTTPS GET open and streams protos down it. A
  Rust framer parses the stream "per //docs/security/rule-of-2.md". Results go back up as
  separate POSTs (`UM:components/browser_actuator/internal/transport/README.md`). The actor
  plugs into it through `ActuationTransportHandler` and `ActorKeyedServiceAdapter`
  (`UM:chrome/browser/actor/transport/`). FACT. This is Google building "the server drives
  your browser", for example from a phone. INFERENCE

### How it integrates with the engine

It is not a fork or a wrapper. It is first-party Chromium code. Features ship behind
`base::Feature` flags with Finch parameters. Examples: `kGlicActor` is on
(`chrome_features.cc:272`), as are `kGlicActorUi` (`:322`) and
`kGlicCrossOriginNavigationGating` (`C:components/actor/core/actor_features.cc:31`). Kill
switches are kept for months, then removed; "Remove kGlicActionUseOptimizationGuide kill
switch" landed on 2026-10-23. FACT

### UI technology and languages

The UI is C++ Views (borders, the task icon, bubbles, the handoff button), plus TypeScript
and Lit WebUI for the overlay and the Glic host. Data types are Mojo IDL and protobuf. The
actions protos are generated inside Google ("DO NOT EDIT… generated in g3",
`actions_data.proto:17-21`). The new transport framer is Rust. FACT

## Data and storage

| Data | Where | Format | Leaves the machine? |
| --- | --- | --- | --- |
| Gemini conversations, plans, task state | Google's servers | proprietary | Yes; that is the design. CLAIM |
| Page context for Glic: APC, viewport screenshot, inner text, PDF bytes | built per request and sent to Gemini | `AnnotatedPageContent` proto, image | Yes, in Chrome (`glic.mojom:387-417`). FACT |
| Actor journal: every step, with optional screenshots | in memory; written to a file with `--actor-trace-path` | `AggregatedJournal` (Perfetto-style trace; parser at `C:components/actor/tools/parse_actor_trace.py`) | Chrome can attach it to feedback (`kGlicRecordActorJournal`, `chrome_features.cc:965-966`). FACT |
| PCES page-content cache | in memory plus SQLite on disk | APC proto | Not by itself. It is off by default and disabled in ungoogled (`H:…/disable-ai.patch`, the `page_content_annotations_service_factory.cc` hunk). FACT |
| On-device model | `<user data>/OptGuideOnDeviceModel` | weights plus a manifest | Downloaded from Google. FACT (path); CLAIM (size) |
| Sensitive-site hints, actor safety lists | the optimization guide hints store; component updater | proto, JSON | Fetched from Google. None of it reaches Helium (`component-updates.patch:144-158`). FACT |
| Glic prefs (`glic.*`), actor UI prefs | `Preferences` JSON | JSON | No. FACT |

**In rac today:** none of Google's flows run. rac calls `GetAIPageContent` directly. It
serializes the result locally and sends text only to the provider the user chose. That
provider is the user's own key, a local model, or an installed agent (`R:docs/internals/ai.md`
"Page context"). FACT

**A cost that is Chromium's, not rac's, with AI off.** `kGlicActor` is on by default, so
every regular profile builds an `ActorKeyedService` at startup. Its factory returns true for
`ServiceIsCreatedWithBrowserContext` (`C:chrome/browser/actor/actor_keyed_service_factory.cc:39-48`).
The service creates a UI state manager, registers a blocklist lookup, and adds an observer
for every download (`actor_keyed_service.cc:151-200`). Every tab also builds `ActorTabData`
and `ActorUiTabController` (`C:chrome/browser/ui/tabs/tab_features.cc:421-435`). These objects
sit idle, because ungoogled empties `GetTaskFromTab` (`H:…/disable-ai.patch:84-100`). FACT.
The cost is small. It has not been measured. INFERENCE

## Agents and AI

### Where the agent runs and what it sees

- **Where it runs:** on Google's servers. Planner, critic, and injection classifier are all
  remote. The browser is a remote executor that sends observations back. FACT (glic.mojom) /
  CLAIM (Google blog)
- **Page representation:** a `TabObservation` that holds the APC proto plus a screenshot.
  Each is voted Skipped, Requested, or Required per action
  (`C:chrome/common/actor.mojom:219-252`). Targets are an APC `dom_node_id` or a coordinate in
  DIPs (`actor.mojom:18-30`). The model-facing description says "The numeric DOM node ID of
  the target element (e.g. 101)" (`UM:…/click_tool_request.cc:28-29`). rac uses its own
  `eN` refs, which are never reused. That is more robust than raw Blink node IDs. FACT /
  INFERENCE
- **Timing defaults:** page stability waits at least 1 s and at most 4 s. The observation
  delay times out after 10 s; the LCP wait is 1 s. Page tools time out after 30 s. The click
  delay is 5 ms (`chrome_features.cc:315-319,423-436`). Script tools time out after 30 s, or
  5 s across documents (`actor_features.cc:164-170`). FACT

### Tools

**In 154, the server's `Actions` proto has 25 kinds** (`actions_data.proto:483-535`): click
(left, right, or "left on occluded target"; single or double), type (replace, prepend, or
append, with Enter), scroll, move_mouse, drag_and_release, select, navigate, back, forward,
wait, create_tab, close_tab, activate_tab, create_window, close_window, activate_window,
yield_to_user, attempt_login, scroll_to, script_tool (WebMCP), media_control,
attempt_form_filling, load_and_extract_content, attempt_otp_filling, and translate_page.
`BuildToolRequest` converts them (`C:chrome/browser/actor/actor_proto_conversion.cc:790-910`).
FACT

**Only 8 run in the renderer**: click, drag_and_release, mouse_move, scroll, select, type,
script_tool, and scroll_to (`C:chrome/renderer/actor/`). Everything else runs in the browser
process inside `ExecutionEngine`. FACT

**On main, a `ToolRegistry` defines 40 tools by ID** (23 at U157), each with a JSON Schema:
navigate, click, switch_tab, scroll, select_option, type, translate_page, go_back, go_forward,
reload_page, seek_to_timestamp, pause_video, play_video, perform_search, exit_fullscreen,
open_known_page, attempt_otp_filling, enter_fullscreen, find_and_highlight, close_tab,
file_upload, create_tab, activate_tab, scroll_to, add_bookmark, remove_bookmark, scroll_page,
create_window, activate_window, close_window, move_mouse, drag_and_release, wait, script,
load_and_extract_content, attempt_form_filling, attempt_login, prompt_gemini_panel,
close_gemini_panel, and open_url (`UM:…/registry/tool_definition.h:19-101`, IDs 0–39). FACT. In
effect, Chrome is converging on an MCP-shaped tool catalog. INFERENCE

### Providers, models, local models

Gemini only. There is no extension point for another planner. Gemini Nano runs only in
Google Chrome: the inference engine sits in the closed `optimization_guide_internal`
library. Public builds set `build_with_internal_optimization_guide = is_chrome_branded`,
which is false for them (`C:components/optimization_guide/features.gni:41-45`). FACT. A
third-party write-up agrees: "if you install `chromium` 148+ from your Linux distribution's
package manager, the Prompt API won't work" ([adsm.dev](https://adsm.dev/posts/prompt-api/)).
CLAIM. ungoogled-chromium goes further and does not build the on-device model service at all
(`fix-building-with-prunned-binaries.patch:107-108`). FACT

### Permissions and safety, layer by layer

| Layer | Chrome (154 code plus Google's description) | rac today |
| --- | --- | --- |
| Who may act | Signed-in, eligible account; country and locale filters; enterprise policy (`C:chrome/browser/glic/actor/glic_actor_policy_checker.cc:93-500`). FACT | AI on, browser control on, regular profile. FACT (`R:docs/internals/ai.md` "Who may act") |
| Which sites | Origin gating. Read-only and read-write "origin sets" chosen by a "trustworthy gating function". The first rollout tracks only the read-write set (CLAIM, Google blog). `kGlicConfirmNavigationToNewOrigins` is on from M158 (FACT) | Named origins, plus `always` and `never` site rules. At `auto`, navigating to a site the user didn't name is free. FACT (`ai.md` levels table) |
| Model-written URLs | "A deterministic check" limits them "to known, public URLs" (CLAIM) | A URL must come from a user message or from a link in a snapshot the model was shown. FACT |
| Sensitive sites | A server list, plus a user confirmation per site (FACT code; the list isn't public) | No site list. Word lists (buy, send, delete…) plus control types. FACT |
| Critic | The "User Alignment Critic" checks every action after planning. It sees "only metadata about the proposed action" (CLAIM) | The critic runs only at `careful`, and also sees metadata only. FACT |
| Injection classifier | Runs "in parallel to the planning model's inference" and "cannot flag everything" (CLAIM) | None. Page text is wrapped in a nonce and labelled untrusted. FACT |
| Time-of-use binding | `observed_target` plus `kGlicActorToctouValidation` (off by default) | Turned on, plus rac's semantic validator and approval binding. FACT |
| Secrets | `attempt_login` and autofill: the user picks, the browser fills, the model never sees the values. FACT (code) | Password and payment fields are always risky, and values are redacted. FACT |
| Red teaming | Automated, LLM-expanded sandboxed attack sites; bug bounty up to $20,000 (CLAIM) | No evals and no red-team suite. FACT (brief) |

### Outside-agent access

- **CDP with per-connection approval** (M144+): `chrome://inspect/#remote-debugging` starts a
  debugging server in "approval mode". The user must approve each incoming connection
  (`C:chrome/browser/devtools/remote_debugging_server.cc:185-247`). The flags
  `--remote-debugging-port` and `--remote-debugging-pipe` are refused on the default
  user-data directory only in Google-branded builds (`:162-183`). FACT. This path gives an
  outside agent full CDP, including `Page.getAnnotatedPageContent` and the `WebMCP` domain,
  with **none of rac's guard**. INFERENCE
- **WebMCP** is the reverse direction: a site publishes tools to whatever agent is in the
  browser. The `untrustedContentHint` and `consequentialHint` annotations are hints the
  *page* writes. Google's own guidance says the browser "can" ask for confirmation on a
  consequential tool, not that it will
  ([developer.chrome.com](https://developer.chrome.com/docs/ai/webmcp/secure-tools)). FACT
- **Browser-side checks for WebMCP permission policy** arrived in commit `cff8d8f`
  (2026-09-25, M156). Before that, a compromised renderer in a disallowed cross-origin
  iframe could advertise tools in APC (commit message). **rac's 154 lacks this fix.** FACT

### Skills and automations

Chrome has Skills (named prompts, synced, and publishable by an admin) and server-started
tasks (`kGlicExperimentalTriggering`, Gemini Spark). Background actuation exists on Android.
Desktop has no local scheduler; scheduling is done on the server. FACT (flags); INFERENCE
(where scheduling lives)

### Exactly what rac's agent patches use

rac does **not** use `ActorKeyedService`, `ActorTask`, `ExecutionEngine`, origin gating, the
actor UI, or Glic. It drives renderer tools directly
(`R:docs/internals/ai.md` "Tools and the action runner";
`C:chrome/browser/rac/agent/renderer_tools.h:25`, "No Glic"). Across rac-created C++ files
(238 non-test `.cc`/`.h`/`.mm` files in the verifier's count; the original said 184 without a
method), 91 lines use `actor::`, `optimization_guide::`, `page_content_annotations::`, or
`AIPageContent` symbols. 36 of them are in `renderer_tools.cc`, 17 in the renderer's
`semantic_validator.{h,cc}`, and 8 in `apc_extract.{h,cc}` (grep). FACT

| Chromium API | rac use | Changes 154 → 156 → main |
| --- | --- | --- |
| `chrome::mojom::ChromeRenderFrame::InvokeTool` and `CancelTool` | Every page action (`C:chrome/browser/rac/agent/renderer_tools.cc:276-336`) | No change (`UM:chrome/common/chrome_render_frame.mojom:121-137`). FACT |
| `actor::mojom::ToolInvocation`, `ToolAction::{NewClick,NewType,NewSelect,NewScroll}`, `ClickAction(kLeft,kSingle)`, `TypeAction::Mode::{kDeleteExisting,kAppend}`, `SelectAction` | Builds each request (`renderer_tools.cc:136-251`) | Click, type, and select: no change. FACT |
| `actor::mojom::ScrollAction(ScrollDirection, float distance)` | Scrolling (`renderer_tools.cc:225-251,282`) | **Breaks in M158.** It becomes `blink.mojom.ScrollDirectionPhysical direction; ScrollAmount amount` (a union of distance or granularity). Commit "actor: Add and implement ScrollPageToolRequest", 2026-10-16. Unchanged in U156 and U157. FACT |
| `ToolInvocation.execution_id` | Not set by rac | Type becomes `blink.mojom.ToolInvocationToken` in M158. FACT |
| `actor::mojom::ObservedToolTarget` with `blink::mojom::AIPageContentAttributes/Geometry`, and `ActionResultCode` values | The time-of-use target and results (`renderer_tools.cc:58-110`) | Additive only. FACT |
| `actor::TaskId::FromUnsafeValue`, `actor::kRootElementDomNodeId`, `actor::MakeResult`, `actor::GetNodeFromId`, `actor::FindFocusedElement`, `actor::ToolBase`, `actor::ResolvedTarget`, `actor::Journal` | Renderer validator and tool hooks | All present at UM (`tool_utils.h:71,98` and others). FACT |
| rac's own `RacActionExpectation` field in `ToolInvocation` | Semantic checks in the renderer | A rac edit (`R:patches/rac/agent/06-guard.patch:1339-1354`). It still applies at U156, U157, and UM (dry run below). FACT |
| `features::kGlicActorToctouValidation` flipped on | Strict time-of-use checking | Upstream is still DISABLED at UM:499. The one-line flip stays necessary. FACT |
| `optimization_guide::GetAIPageContent`, `ActionableAIPageContentOptions`, `DefaultAIPageContentOptions`, `GetRenderFrameForDocumentIdentifier`, `proto::AnnotatedPageContent` | Chat, the agent, link summaries | **`AIPageContentResultOrError` changes in M158**, from `expected<…, std::string>` to `expected<…, AIPageContentError{status, message}>` ("[PageContext] Propagate extraction error enums", 2026-10-16). rac uses the type in 10 places across 9 files. At least 2 call sites pass `.error()` on as a string (`R:patches/rac/ai/15-page-text.patch:580-582`, `R:patches/rac/agent/03-actions.patch:957-963`). Still `std::string` at U156 and U157. FACT |
| `common_quality_data.proto` (APC fields) | The serializer | 128 lines changed 154 → UM. Removals are limited to `gemini_in_chrome_page_metadata`, `screenshot_info`, and `CLICKABILITY_REASON_MOUSE_HOVER`. FACT. None of these appear to be used by rac. INFERENCE (grep of the serializer) |
| `page_content_annotations::PageSettledMonitor` | Settle after each action, 4 s cap | 0 lines changed to UM. FACT |
| Context-only anchors: `ActorNavigationThrottle::MaybeCreateAndAdd`, `kGlicBlockFileSystemAccessApiFilePicker`, `kGlicActorIncrementalTypingWaitForEditableElement`, `optimization_guide::PageTextAgent` | Hook placement | Present at UM. FACT |

**Edits to upstream files:** in total, `R:patches/rac/agent/*.patch` edits 21 upstream files
with 58 hunks and about 207 changed lines (198 added, 9 removed). The Chromium-agent subset is
13 files, 40 hunks, and about 158 lines:
`chrome/renderer/actor/{type_tool,key_dispatcher,click_dispatcher,tool_base,tool_executor}`
(`.cc` and `.h`), `chrome/renderer/actor/BUILD.gn`, `chrome/common/actor.mojom`,
`chrome_features.cc`, `chrome_render_frame_observer.cc`, `web_local_frame_impl.cc`, and the
throttles file. The other 8 are hooks outside the actor code:
`chrome_content_browser_client.cc`, `chrome_download_manager_delegate.cc`,
`browser_web_contents_delegate.cc`, `settings_private/prefs_util.cc`, and four `BUILD.gn`
files. FACT (verifier's count; "upstream" = not created by any `R:patches/rac/` patch)

**Dry run.** I extracted rac's hunks per file and ran `patch --dry-run` against the upstream
file at each tag (`/tmp/rac-overhaul/scripts/dry.sh`):

| File | 154 | 156 | 157 | main |
| --- | --- | --- | --- | --- |
| `type_tool.cc` (332 upstream lines changed) | clean | clean | clean | clean |
| `key_dispatcher.cc` | clean | 1 of 7 fail | 1 of 7 | 1 of 7 |
| `click_dispatcher.cc` | clean | 1 of 4 | 1 of 4 | 1 of 4 |
| `tool_base.cc` (`ExecutionObservationDelay()` removed upstream, 2026-09-02) | clean | 1 of 1 | 1 of 1 | 1 of 1 |
| `tool_base.h`, `tool_executor.cc`, `actor.mojom` | clean | clean | clean | clean |
| `chrome_render_frame_observer.cc` | clean | 1 of 2 | 1 of 2 | 1 of 2 |

FACT. Caveat: this checks text only. It is not a compile, and it ignores ordering between
patches. INFERENCE

**Churn by milestone window** (commits that landed on main between branch points):

| Path | M155 | M156 | M157 | M158 so far |
| --- | --- | --- | --- | --- |
| `chrome/browser/actor` | 67 | 79 | 148 | 111 |
| `components/actor` | 7 | 5 | 18 | 23 |
| `chrome/browser/glic` | 140 | 231 | 218 | 167 |
| `core/script_tools` (WebMCP) | 3 | 6 | 5 | 13 |
| Blink APC | 0 | 2 | 7 | 10 |
| `chrome/renderer/actor` | 11 in total | | | |

FACT. The big M157 and M158 refactors are in layers rac skips: `ActorSurface` replaces
`TabHandle` as the target, the `ToolRegistry`, the transport, the tool directories moved
under `tools/{autofill,password_manager,one_time_token}`, and new tools.

**APC meaning drift that unit tests won't catch.** "[APC] Add label sources and remove
repeated text" (2026-10-03) adds title, alt, CSS alt, and SVG title as label sources. It
also drops a label that duplicates its child text. "[APC] Omit FormControlData::field_value
for checkbox and radio inputs" (2026-09-25). MathML support (2026-10-19). "Omit unknown ARIA
roles" (2026-10-14). `<summary>` now appears as an expandable button (2026-10-06). FACT. rac's
`ControlName` falls back to the node's text when `label` is empty
(`C:chrome/browser/rac/agent/snapshot_serializer.cc:225-251`), so names should survive.
Snapshot text and ref names will still shift, and rac's serializer tests use synthetic protos
that can't see any of it. INFERENCE

**Risk judgment.**

- **Low** for rac's chosen layer: renderer tools, APC, and the page-settled monitor. Expect
  about 4 failed hunks and 2 compile fixes (scroll, APC error type) on the way to M158, about
  1–2 days of work. INFERENCE (from the dry run and the API diff)
- **Medium** for meaning drift in APC output, because nothing tests it against real pages.
  INFERENCE
- **High** if rac ever adopted `ExecutionEngine`, `ActorKeyedService`, or Glic. Those need
  Safe Browsing on, Google hints and components, and account checks. They change at 4–8
  commits a day, and Helium prunes them. INFERENCE
- **A tail risk:** Helium or ungoogled could disable `kGlicActor` to save idle objects, and
  the renderer CHECK would then crash rac's agent. A rac patch that keeps `kGlicActor` on
  (or removes the CHECK) prevents it. INFERENCE

### Built-in AI APIs in an ungoogled build

| API | Web-exposed in 154? | Works in rac? | Why |
| --- | --- | --- | --- |
| Prompt (`LanguageModel`), with multimodal input, structured output, and tool use (experimental) | Yes on Mac (`AIPromptAPI` stable) | No | The on-device model service isn't built (ungoogled), the inference library is closed, and components are blocked (Helium allows CRLSet and Widevine only). FACT |
| Summarizer, Writer, Rewriter, Proofreader | Summarizer stable; the others behind trials | No | Same reasons. FACT |
| Translator, Language Detector | Yes; `TranslationAPI` and `LanguageDetectionAPI` are "stable" on Mac (`C:…/runtime_enabled_features.json5:6442-6450,3789-3798`). FACT | No | The TranslateKit and language-detection models come through the component updater, which Helium blocks. FACT (allowlist). Helium has its own macOS translation for selected text (`plans/research/helium.md`). |
| `--optimization-guide-ondevice-model-execution-override` | n/a | No | It only points the closed library at local weights (`C:components/optimization_guide/core/optimization_guide_switches.cc:18-19`). Without the library and the service there is nothing to run. FACT |

## Build, release, and engineering

- **Build:** GN plus siso. Feature code sits behind `base::Feature` flags with Finch
  parameters. Two things keep Finch out of rac. Bromite's
  `disable-fetching-field-trials.patch` stops the variations service from fetching seeds
  (`R:helium-chromium/patches/series:38`). `disable_fieldtrial_testing_config=true`
  (`R:helium-chromium/flags.gn:3`) drops the in-tree testing config
  (`C:components/variations/service/BUILD.gn:8-14`). So a feature Google enables only through
  Finch stays at its source default in rac. FACT. This is why WebMCP or Prompt API launches
  done through Finch would not reach rac. INFERENCE
- **CI and tests:** heavy. `chrome/browser/actor` has more test lines (39,362) than code
  (32,578). Glic has `interactive_uitest` suites per tool (`C:chrome/browser/glic/host/glic_actor_*_interactive_uitest.cc`,
  16 files, plus 2 shared `glic_actor_interactive_uitest_common` files). FACT
- **AI-assisted engineering upstream:** "[Actor] Opt in to Chromium AI Code Review"
  (2026-10-20). APC opted in too. The repo ships an agent skill for registering tools. FACT
- **Release:** Chrome's two-week train. Kill switches are removed after launch, for example
  `kGlicActionUseOptimizationGuide` (2026-10-23) and `kGlicEarlyAddTaskTabs` (2026-10-15).
  FACT
- **How rac tracks it:** quilt patches on Helium's tree. The agent patches are a small share
  of rac's sync problem: Helium's dossier counts 59 of 180 rac patches failing on 0.20.1.1,
  mostly UI (`plans/research/helium.md`). FACT

## Strengths and weaknesses

**Strengths**

1. **APC is very good input for agents.** It walks the layout tree and reports geometry and
   occlusion. It redacts passwords, payments, and one-time codes, lists iframes with their
   origins, and now carries WebMCP tools. rac gets all of this for free. FACT
2. **The renderer tools are hard-won.** They handle occluded targets, incremental typing,
   zero-area targets, and time-of-use validation, with UAF fixes still arriving. The layer is
   stable: 11 commits in 55 days. FACT
3. **The safety design is the industry reference.** It has origin sets, a critic that sees
   only metadata, deterministic URL checks, sensitive-site prompts, and secret-free login.
   rac's guard already matches several of these ideas. CLAIM (Google) / FACT (rac)
4. **Outside-agent plumbing ships in the engine.** CDP approval mode, `getAnnotatedPageContent`,
   and the WebMCP CDP domain are all there. FACT

**Weaknesses**

1. **It is built around Google.** It needs a Google account, Safe Browsing, server-side
   lists, server-side models, and a server-side critic. Inside an ungoogled build, every one
   of these fails closed (Safe Browsing) or fails open (sensitive sites). FACT
2. **Churn.** About 7 commits a day in `chrome/browser/actor` and 14 in Glic. The core target
   type (`TabHandle` → `ActorSurfaceHandle`) and the proto pipeline (→ `ToolRegistry` plus
   transport) changed within two milestones. FACT
3. **The safety-critical time-of-use check is still off by default** at `main`. FACT
4. **The UI is noisy and repaints continuously.** It ignores reduced motion for the spinner
   and the glow. FACT
5. **WebMCP's safety rests on page-authored hints**, and the browser-side permission-policy
   enforcement only arrived in M156. FACT

## What rac should take (ranked, with rough cost) and what rac should avoid

**In plain words.** Keep using Chrome's two lowest layers. Copy Google's safety ideas, not
its code. Let pages offer tools to rac's agent, but treat them as untrusted. Fix the M158
breaks before they arrive. Costs: **S** is up to 3 days, **M** is 1–2 weeks, **L** is 3
weeks or more.

### Take

1. **Ask before the first visit to a new site at `auto`.** This closes the exfiltration
   chain the brief describes. At `auto`, the first navigation or cross-site link click to an
   origin outside the task's named set gets one card. After that the site counts as named
   for the turn. Chrome made this its default on 2026-10-19 (`8799124`, FACT). The commit gives
   no reason beyond a bug link, so "for the same reason" is INFERENCE.
   Typing model-written text should then ask on any site that was not named by the *user*;
   sites the agent named don't count. **Cost S.** (Change `ActionGuard`'s level table, and
   add the matching tests to `AutoAsksOnlyForRiskAndForeignTyping`.)
2. **Build the pin-and-dry-run harness before the Helium sync.** A script like
   `/tmp/rac-overhaul/scripts/dry.sh` checks rac's upstream hunks against the next Chromium
   tag. A small `static_assert`/compile test pins `ScrollAction`, `AIPageContentResultOrError`,
   and `InvokeTool`. Pre-port the two known M158 breaks behind
   `#if CHROME_VERSION_MAJOR >= 158`, or just fix them during the 158 sync. **Cost S.**
3. **Keep every Chromium AI symbol behind two rac files.** `renderer_tools.{h,cc}` and
   `apc_extract.{h,cc}` already hold 47 of the 91 uses. Move the rest of `snapshot_serializer`'s
   proto reads and `link_fetcher`/`page_context`'s result handling behind them. **Cost S–M.**
4. **Read-only origin set for page content.** Leave content from cross-origin iframes whose
   origin isn't in the task's set out of the agent's snapshot and page text, or show it only
   as a labelled stub. That is Google's "If an iframe's origin isn't on the list, the model
   will not see that content". APC already gives each frame's origin. **Cost M.**
5. **Let rac's agent use WebMCP page tools, after syncing to ≥156** (for the permission-policy
   fix `cff8d8f`). List the frame's `script_tools` in the snapshot as untrusted lines, for
   example `- page tool "add_to_cart" [ref=t3] (consequential)`. Add a `call_page_tool`
   action that sends `ToolAction::NewScriptTool` over the existing `InvokeTool` path. Treat
   *every* page tool as a click on a named site. `consequentialHint` or a missing
   `readOnlyHint` puts it on the risky list. Wrap tool output with the page-text nonce. Serve
   the same tools to outside agents through rac's MCP. Optionally turn on `WebMCP` with a
   feature override so pages work without a trial token. **Cost M.**
6. **Real-page snapshot tests.** Save about 30 real pages as MHTML, or a local corpus. Run
   them through the actual APC extractor in a browser test, and diff the serialized snapshot
   on each sync. This catches the label and checkbox changes listed above. **Cost M.**
7. **A local, shipped sensitive-site list.** Add a small curated list of banks, health,
   government, payments, and email sites, built into rac with no network. Use it to make
   "first action on this site" a risky card at every level, as Chrome's deterministic list
   does. Add a `--rac-agent-sensitive-sites=` switch for tests, modelled on
   `--actor-sensitive-sites`. **Cost S–M** (the list is the work).
8. **Run traces as the basis for evals and red-teaming.** Record each turn's tool calls,
   guard decisions, page hashes, and card answers to a local JSON or Perfetto file behind a
   switch, modelled on `--actor-trace-path` and `parse_actor_trace.py`. Replay injection pages
   against it in CI. **Cost M.**
9. **Secret-free login, later.** Chrome's `attempt_login` pattern: the model asks to sign in,
   rac shows the user a credential picker, and the browser fills it. The model never sees the
   password. Use it only if it can be built on `password_manager` without `ExecutionEngine`.
   Whether that is possible is open. **Cost L.**
10. **A calm acting cursor.** The good idea in Chrome's UI is showing *where* the agent will
    act. Add a static marker at the target, a move of at most 300 ms with
    `cubic-bezier(0.6,0,0.4,1)`, and a 400 ms press. Skip the glow, idle loops, and infinite
    animations, and turn it all off under reduced motion. **Cost S–M** (goes to the UI
    thread, on Opus).
11. **Use Chrome's tool names in rac's MCP tools:** `navigate`, `click`, `type`,
    `switch_tab`, `open_url`, `scroll`, `select_option`, `go_back`. Outside agents trained on
    Chrome's catalog will then guess right. **Cost S.**
12. **Document the CDP approval path as an advanced option**, not the default way for outside
    agents to connect. It works with AI off and costs nothing when off. Say plainly that it
    bypasses rac's guard. Verify that `chrome://inspect/#remote-debugging` works in rac and
    record the `DevToolsActivePort` location under rac's profile. **Cost S.**

### Avoid

- **Adopting `ExecutionEngine`, `ActorKeyedService`, Glic, or the browser actuator.** Almost
  every action is blocked without Safe Browsing (`execution_engine.cc:423-437`). The only
  bypass in the gating list, `--disable-actor-safety-checks`, turns off every other safety
  check too. The safety data
  comes from Google, and the layer churns daily.
- **Reviving Gemini Nano or the built-in AI web APIs.** The library is closed, the service
  isn't built, components are blocked, and the model license is Google's.
- **Backing the web-exposed Prompt API with the user's key or local model.** Every website
  would spend the user's key or compute, and availability would fingerprint the user. It also
  conflicts with "AI off costs nothing" unless it is tightly gated.
- **Turning on PCES automatic extraction.** It extracts every page on load, which breaks
  "AI off costs nothing".
- **Disabling `kGlicActor` to save the idle actor objects.** The renderer CHECKs it
  (`tool_executor.cc:45`).
- **Relying on optimization-guide sensitive-site hints.** They fail open in Helium
  (`site_policy.cc:53-62`).
- **Trusting WebMCP descriptions or annotations, or using WebMCP on 154** (no browser-side
  permission-policy check).
- **Copying Chrome's ever-pulsing glow, its spinner that ignores reduced motion, or its
  seven-surface status UI.**

## Open questions and things you could not verify

1. **No compile was done.** The dry run tests patch text only. The real cost of moving to
   156 or 158 needs a worktree build, which needs the maintainer's approval.
2. **Idle cost of Chromium's actor objects with AI off** (`ActorKeyedService`, the download
   observer, two objects per tab). Not measured.
3. **WebMCP's ship date.** Third parties say Chrome 157 turns it on by default (CLAIM, the
   PostHog PR cited in search results). Source at U157 and UM still says `status:
   "experimental"`, and chromestatus lists no ship milestone (only the 149–156 origin trial).
   A Finch launch would not reach rac (field trials are off). Unresolved.
4. **Whether `chrome://inspect/#remote-debugging` approval mode works in rac and Helium**, and
   where `DevToolsActivePort` lands. Not run.
5. **Whether `LanguageModel` is exposed in rac pages** and what `availability()` returns. Not
   run (INFERENCE: "unavailable").
6. **Whether `ActorLoginService` and Autofill's actor form filling can be used without
   `ExecutionEngine`.** Not traced.
7. **Google's server-side planner, critic, classifier, and red-team suite** can't be
   inspected. The safety claims are Google's own.
8. **The sensitive-site list contents** (`GLIC_ACTION_PAGE_BLOCK`) are not public. A rac
   list would have to be built from scratch.
9. **Whether later Helium releases prune more actor code.** As of HL `f29a259`, only WebUI
   resources and Skills are removed. The actor renderer code is intact.
10. **The commit counts** use GitHub's path-filtered history. Renames may slightly over- or
    under-count.

## Sources

Local, read-only (Chromium 154 with Helium and rac): `C:chrome/browser/actor/{README.md,
actor_keyed_service.{h,cc}, actor_keyed_service_factory.cc, actor_task.h, execution_engine.cc,
site_policy.cc, actor_proto_conversion.cc, tool_request_variant.h, tools/*}`,
`C:chrome/renderer/actor/*`, `C:chrome/common/actor.mojom`, `C:chrome/common/chrome_features.cc`,
`C:components/actor/core/{actor_features.cc, actor_switches.cc, actor_util.cc,
safety_list_manager.h}`, `C:components/origin_gating/core/actor_container_config.h`,
`C:components/optimization_guide/proto/features/actions_data.proto`,
`C:components/optimization_guide/content/browser/page_content_proto_provider.h`,
`C:components/page_content_annotations/content/pces_guide.md`,
`C:third_party/blink/public/mojom/content_extraction/{ai_page_content.mojom, script_tools.mojom}`,
`C:third_party/blink/renderer/modules/content_extraction/readme.md`,
`C:third_party/blink/renderer/core/script_tools/*.idl`,
`C:third_party/blink/renderer/platform/runtime_enabled_features.json5`,
`C:third_party/blink/public/devtools_protocol/domains/{Page.pdl, WebMCP.pdl}`,
`C:chrome/browser/devtools/remote_debugging_server.cc`, `C:chrome/browser/glic/host/glic.mojom`,
`C:chrome/browser/glic/public/glic_enabling.cc`, `C:chrome/browser/glic/browser_ui/*.cc`,
`C:chrome/browser/resources/actor_overlay/{app.css, app.ts}`, `C:chrome/app/actor_strings.grdp`,
`C:components/policy/resources/templates/policy_definitions/GenerativeAI/*.yaml`,
`C:components/optimization_guide/features.gni`, `C:services/on_device_model/on_device_model.gni`,
`C:out/Default/args.gn`, `C:chrome/browser/rac/agent/*`, `C:chrome/renderer/rac/agent/*`.

rac and Helium: `R:docs/internals/ai.md`, `R:patches/rac/agent/*.patch`,
`R:helium-chromium/patches/ungoogled-chromium/{disable-ai.patch, fix-building-with-prunned-binaries.patch}`,
`R:helium-chromium/patches/helium/core/{component-updates.patch, degoogle-context-menu.patch}`,
`R:helium-chromium/domain_substitution.list`,
`HL:patches/helium/core/remove-unused-ai-resources.patch`, `R:plans/research/helium.md`,
`R:plans/research/closed-ai-browsers.md`.

Upstream (GitHub mirror `chromium/chromium`, read-only `gh api`): tags `154.0.8037.92`,
`156.0.8078.48`, `157.0.8103.15`; `main` at `edd107109066a4cf754f4b2b6005bbe0c5714341`.
Files: `chrome/common/{actor.mojom, chrome_render_frame.mojom, chrome_features.cc}`,
`components/optimization_guide/content/browser/{page_content_proto_provider.h, page_content_proto_util.h}`,
`chrome/browser/actor/tools/registry/{README.md, tool_definition.h}`,
`chrome/browser/actor/tools/{navigate,click,type,switch_tab,open_url}_tool_request.{h,cc}`,
`chrome/browser/actor/transport/actor_keyed_service_adapter.h`,
`components/browser_actuator/{README.md, internal/transport/README.md}`,
`components/actor/core/actor_switches.cc`. Commits `8799124`, `a84713b`, `046af97`, `cff8d8f`,
`c34b574`, and the commit lists in `/tmp/rac-overhaul/work/commits_*.tsv`. Release data:
<https://chromiumdash.appspot.com/fetch_releases>, <https://chromiumdash.appspot.com/fetch_milestones>,
<https://cr-rev.appspot.com>.

Web:
- Google, "Architecting security for agentic capabilities in Chrome" (2025-12-08): <https://blog.google/security/architecting-security-for-agentic/>
- Chrome for Developers, "WebMCP tool security" (updated 2026-09-01): <https://developer.chrome.com/docs/ai/webmcp/secure-tools>
- Chrome for Developers, "Imperative API" (WebMCP): <https://developer.chrome.com/docs/ai/webmcp/imperative-api>
- WebMCP spec draft: <https://webmachinelearning.github.io/webmcp/>; repo <https://github.com/webmachinelearning/webmcp>
- 9to5Google, Chrome auto browse launch (2026-01-28): <https://9to5google.com/2026/01/28/chrome-gemini-auto-browse/>
- CNBC (2026-01-28): <https://www.cnbc.com/2026/01/28/google-brings-more-gemini-ai-features-to-chrome-browser-.html>
- aiagentslibrary, auto browse pricing and caps (CLAIM): <https://www.aiagentslibrary.com/blog/gemini-spark-chrome-auto-browse/>
- adsm.dev, "The Prompt API is now on by default in Chrome" (CLAIM about non-Google builds): <https://adsm.dev/posts/prompt-api/>
- dev.to, Gemini Nano hardware requirements (CLAIM): <https://dev.to/max_quimby/chromes-gemini-nano-prompt-api-a-step-by-step-guide-26n3>
- SecurityWeek coverage of Chrome agent defenses: <https://www.securityweek.com/google-fortifies-chrome-agentic-ai-against-indirect-prompt-injection-attacks/>
- WebMCP origin-trial reports (CLAIM): <https://dev.to/thousand_miles_ai/webmcp-in-chrome-149-web-pages-get-a-tool-api-for-ai-agents-bfi>, <https://mcpplaygroundonline.com/blog/what-is-webmcp>
- chrome-devtools-mcp `--autoConnect` docs (local clone `ada7963`): `/tmp/rac-overhaul/src/chrome-devtools-mcp/docs/advanced-usage.md:55-101`, `docs/configuration.md:67-70`

## Verification

Adversarial fact-check, 2026-10-25. Sources: the read-only tree at C:, this worktree (R:),
`gh api` reads of `chromium/chromium` at the three tags and `edd1071`, `gh api` reads of
`imputnet/helium` tags, chromiumdash, chromestatus, and Google's own pages. Only text in patches
and upstream files was compared. Nothing was built or run. "OK" means the claim matched the
primary source as written.

| # | Claim | Result | Change made |
| --- | --- | --- | --- |
| 1 | C: is Chromium 154.0.8037.92 with Helium 0.18.2.1 (`C:chrome/VERSION`) | OK | none |
| 2 | Stable 156.0.8078.48, Beta 157.0.8103.15, Canary 158.0.8124.0; branch points 154 to 157 | OK (chromiumdash `fetch_releases`, `fetch_milestones`; branch hashes dated with `gh api`) | Added 153, 152, and 151 branch dates; "ships every two weeks since M153" reworded to "branches every two weeks from M153 on" |
| 3 | `BlockIfSafeBrowsingDisabled` at `execution_engine.cc:423-437`; `safe_browsing_mode=0` sets `SAFE_BROWSING_AVAILABLE=false` | OK on lines. Overstated as "blocks everything" | Now says it is predicate 9 of 19, for navigation requests and page actions only. about:blank, localhost requests, and `--disable-actor-safety-checks` are decided earlier. Cited release flags `R:helium-chromium/flags.gn:14` too |
| 4 | Origin gating is 19 ordered predicates over 3 event types (`execution_engine.cc:683-760`) | OK (counted 19) | none |
| 5 | `kGlicActorToctouValidation` is DISABLED upstream at 154, U156 (`:479`), U157 (`:477`), UM (`:499`); rac flips it | OK | Patch line range corrected to `03-actions.patch:2139-2148` |
| 6 | `ToolExecutor` CHECKs `kGlicActor` (`C:chrome/renderer/actor/tool_executor.cc:45`), and `InvokeTool` builds it unconditionally | OK (`C:chrome/renderer/chrome_render_frame_observer.cc:685-693`) | none |
| 7 | 25 action kinds in the `Actions` proto (`actions_data.proto:483-535`), and "generated in g3" | OK (fields 1 to 25; "Next ID: 26") | none |
| 8 | 8 renderer tools | OK (`actor.mojom` `union ToolAction`, 8 members) | none |
| 9 | `ToolRegistry` has 30 tool IDs on main | **Wrong.** 40 IDs (0 to 39) at `edd1071`; 23 at U157 | Fixed count and list in two places; status now "from M157" |
| 10 | `switch_tab`, `perform_search`, `open_known_page`, `open_url` "landed in M157 and M158" | **Partly wrong.** `switch_tab` and `perform_search` exist at U156 | Fixed per tool, with `gh api …/contents?ref=` checks |
| 11 | Headless `ActorSurface` work is M157 and M158 | Partly wrong. `31cd13c8` landed 2026-09-28T20:30Z, before the M156 branch | Now M156 to M158, with SHAs |
| 12 | `ScrollAction` becomes `ScrollDirectionPhysical` plus `ScrollAmount` on main (`d25c378`, 2026-10-16); unchanged at U156 and U157; `execution_id` becomes `ToolInvocationToken` (`8fc7765`) | OK | none |
| 13 | `AIPageContentResultOrError` becomes `expected<…, AIPageContentError>` on main; still `std::string` at U156 and U157; rac uses it in 10 places across 9 files | OK (`page_content_proto_provider.h` at each ref; grep of `C:chrome/{browser,renderer}/rac`) | none |
| 14 | Commit `cff8d8f` (WebMCP permission policy) is in M156, not 154 | OK. Position 1705317 is before the 156 branch (1706539). `PermissionsPolicyFeature::kTools` appears in `script_tool_host.cc` at U156, not at 155.0.8059.86 or C: | none |
| 15 | Commits `8799124` (2026-10-19, new-origin confirm on), `a84713b` (per-site cache), `c34b574` ("almost-purely restrictive"), `046af97`, `5b0f8ecb`, `a4476cfb` | OK | Tagged the "for the same reason" motive behind `8799124` as INFERENCE; the commit message gives none |
| 16 | Churn since 154 branch: 405 / 756 / 53 / 27 / 19 / 11 commits; 87 and 162 unique authors | OK (re-counted with `gh api --paginate` at `edd1071`) | none. The per-milestone table was not re-counted |
| 17 | OWNERS: 13 actor, 5 Glic | **Glic wrong.** Glic's OWNERS includes `components/glic/OWNERS`, which lists 8 | Fixed |
| 18 | Code-size line counts | **Not reproducible** with the unstated method. A `.cc`/`.h` recount differs by 0% to 40% | Replaced with the recount and its method |
| 19 | Helium allows only CRLSet and Widevine components; rac adds none | OK (`component-updates.patch`; no rac patch touches the allowlist; `C:components/component_updater/component_installer.cc:112-118`) | none |
| 20 | ungoogled sets `use_on_device_model_service = false`; `build_with_internal_optimization_guide = is_chrome_branded`; the library is `optimization_guide_internal` | OK | none |
| 21 | Glic needs a signed-in account | OK on desktop. `kGlicShowForSignedOut` is on only for Android (`C:chrome/browser/glic/public/features.cc:221-226`), and it only shows a sign-in promo | none |
| 22 | Motion values: glow `inset 0 0 35px 12px`, 4000 ms infinite, no reduced-motion guard; cursor 1.5 px/ms, 50 to 300 ms, `cubic-bezier(0.6,0,0.4,1)`; click 400 ms; thinking 750 + 3200 ms; fade 200 ms; Glic border 500/1500/1000 ms; selection 250 ms; underline 3000 ms | OK (`app.css`, `app.ts:244-260`, `chrome_features.cc:370-379`, Glic `browser_ui/*.cc`). No reduced-motion check for the glow in `app.css` or `chrome/browser/actor/ui` | "Repaints forever" softened: it is an opacity loop the compositor can usually run, which still produces frames |
| 23 | Glic animated effect "uses a simplified shader under reduced motion" | **Mislabelled.** Reduced motion sets `skip_animation_cycle_`: no cycle, still effect, 200 ms fade-in | Fixed |
| 24 | Debounce "25 ms per event" | Imprecise. It is for hover events on the overlay and handoff button | Fixed |
| 25 | `ActorKeyedService` is built with every regular profile; it inits the blocklist and a download notifier; tabs build `ActorTabData` and `ActorUiTabController`; ungoogled empties `GetTaskFromTab` | OK | none |
| 26 | Page tool timeout 30 s, click delay 5 ms, page stability 1 to 4 s, observation 10 s, LCP 1 s, script tools 30 s / 5 s | OK | none |
| 27 | rac's agent patches edit 13 upstream files, 38 hunks, about 155 lines | **Undercounted.** 21 upstream files, 58 hunks, about 207 lines. The 13 actor-path files hold 40 hunks and about 158 lines | Fixed, listing the 8 omitted files |
| 28 | 91 lines across "184 rac-owned source files" use Chromium AI symbols; 36 / 17 / 8 split; 47 in two wrapper pairs | Numerator and split OK. Denominator not reproducible (238 non-test rac-created C++ files) | Fixed denominator |
| 29 | Dry run: rac's `tool_base.cc` hunk fails from U156 because `ExecutionObservationDelay()` was removed (`17edd297`, 2026-09-02); `actor.mojom` hunks still apply | OK (own `patch --dry-run` against the files fetched with `gh api`) | none. The other rows were not re-run |
| 30 | `common_quality_data.proto`: 128 changed lines from 154 to UM; only three removals; rac uses none of them | OK (diff; grep of rac sources) | none |
| 31 | `PageSettledMonitor` unchanged from 154 to UM | OK (0 diff lines in `.h` and `.cc`) | none |
| 32 | Helium removed `chrome://actor-internals` in 0.19.3.1 | OK. `aec023c` (2026-10-09) is first in Helium core tag 0.19.3 (`gh api …/compare`) | none |
| 33 | Finch launches don't reach rac because of `disable_fieldtrial_testing_config` | **Wrong mechanism.** That flag only drops the in-tree testing config. Bromite's `disable-fetching-field-trials.patch` (`series:38`) is what stops the seed fetch | Fixed |
| 34 | WebMCP origin trial 149 to 156 (was CLAIM) | Confirmed by chromestatus (feature 5117755740913664, origin-trial stage 149 to 156; ship stage blank) | Re-tagged FACT; open question 3 updated |
| 35 | Gemini Nano needs about 22 GB (was CLAIM) | Confirmed by Chrome for Developers | Re-tagged FACT with the official link and the full hardware needs |
| 36 | Translator and Language Detector "stable in Chrome" (was CLAIM) | Confirmed in source (`runtime_enabled_features.json5`) | Re-tagged FACT. Writer, Rewriter, and Proofreader statuses also spelled out |
| 37 | Google blog: critic sees only metadata; iframe sentence; "known, public URLs"; classifier runs in parallel; up to $20,000; first rollout tracks only the read-writable set | Quotes match the 2025-12-08 post. They remain CLAIM (vendor self-report) | none |
| 38 | `developer.chrome.com` WebMCP security: extensions can query and execute tools through content scripts; the browser "can" request confirmation | OK (page updated 2026-09-01) | none |
| 39 | Glic interactive UI tests: 19 files | **Wrong.** 16 test files, plus 2 shared helper files | Fixed |
| 40 | Remote debugging approval mode; default-profile refusal only in Google-branded builds | OK in code (`remote_debugging_server.cc:162-183`). Not run in rac, which is still INFERENCE | none |

**Not checked:** the milestone-window churn table, the dry-run rows for `key_dispatcher`,
`click_dispatcher`, and `chrome_render_frame_observer`, the third-party pricing and launch
reports (still CLAIM), `glic_actor_policy_checker.cc` details, and the APC drift commit titles
from 2026-09-25 to 10-19.

**What a plan should take from this.** The main conclusions stand. Safe Browsing gating makes
Chrome's task engine unusable in rac. Glic needs a Google account. Gemini Nano cannot run. The
two M158 compile breaks are real, and rac's chosen layer churns little. The corrections are
mostly counts that were too low: tool IDs (40, not 30) and rac's upstream edits (21 files, not
13). Plans that cost the next Helium sync should use the higher edit count.

**Overall confidence: high** for the architecture, gating, and API-break claims, which were
re-checked line by line. **Medium** for the counts, dates, and labels. Eleven of the 40 checks found a
wrong, partly wrong, or mislabelled claim (rows 9, 10, 11, 17, 18, 23, 24, 27, 28, 33, 39),
and all were fixed.
