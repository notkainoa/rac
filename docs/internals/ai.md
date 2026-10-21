# AI

This page records the decisions behind rac's AI, the constraints that span
several patches, and the traps that are hard to see in the source. It does
not describe what the code plainly says. Read the code for that.

The AI lives in two patch groups: `patches/rac/ai/` (the assistant) and
`patches/rac/agent/` (browser control). Their code is under
`chrome/browser/rac/ai/` and `chrome/browser/rac/agent/`.

## Settled

These come from [VISION.md](../../VISION.md) and hold for every change:

- AI is off by default (`rac.ai.enabled`, default false). You can turn it on
  or off in settings at any time. Onboarding, which isn't built yet, will ask
  whether you want it.
- When AI is off, none of its code does any work: no processes, no network
  calls, no background tasks. See [AI off costs nothing](#ai-off-costs-nothing).
- rac never sees AI conversations. Only the user and their chosen provider
  do. There is no rac-hosted AI service.
- The agent never takes an action in the browser without the user's
  confirmation. In practice that means an approved plan for the first
  action, and a confirmation for every consequential one. See
  [The guard](#the-guard).
- AI is for regular profiles only. Incognito gets no assistant panel, no
  agents, no link summaries, and no find-in-page Ask. Any new AI feature
  must check this itself. Link summaries once ran in Incognito because they
  looked up the original profile's setting.
- Page content is untrusted. It is never allowed to give instructions to the
  assistant, and it never reaches the agent's safety check.

## How it's built

| Group | Owns |
| --- | --- |
| `rac/ai/01`–`13` | Settings and prefs, direct providers, the assistant side panel, page attachment, history and saved prompts, the new tab page, native menus, the right-edge pull handle |
| `rac/ai/14`–`16` | The AI-off audit, page text extraction, hidden-text filtering |
| `rac/ai/17`, `18` | Find-in-page Ask, new tab page auto-pick |
| `rac/ai/19` | Link summaries |
| `rac/ai/20`–`23` | The ACP client, agent providers, agent settings, agent progress in the chat |
| `rac/agent/01`–`03` | Page snapshot and refs, tool definitions, the action runner |
| `rac/agent/04`, `08` | The MCP server for ACP agents, and the adapter that serves the agent's tools through it |
| `rac/agent/05`–`07` | The direct-provider tool loop, the guard, the critic |
| `rac/agent/09`–`11` | Confirmation cards, the tab indicator, and the wiring between them and the controller |
| `rac/agent/12` | Hardening: the checks that close the gaps found in review |

### Providers

The assistant talks to one of three kinds of provider.

- **Your own key.** OpenAI, Anthropic, Google Gemini, OpenRouter, or a custom
  OpenAI-compatible endpoint. Keys are encrypted with `os_crypt_async`
  before they reach prefs. A base URL must be `https`, or `http` only for
  localhost, with no credentials, query, or fragment.
- **A local model.** Ollama or LM Studio, through their OpenAI-compatible
  endpoints.
- **An installed agent.** Claude Code, Codex, Cursor, Gemini, Copilot,
  OpenCode, Goose, or a custom ACP command. rac runs the user's own CLI, so
  the user's own subscription pays. See [ACP agents](#acp-agents).

The direct providers (the first two kinds) are the only ones that can run
the agent's safety check. An agent is a provider for chat, and also a
source of browser tool calls, but it is never asked to judge its own
actions.

The model menu asks each set-up provider for its model list when the menu
opens, and Settings asks only while the Assistant page itself is open (a
settings search renders the section too, and must not send the key):
OpenAI-compatible servers `GET {base}/models`, Anthropic
`GET {base}/v1/models`, always with the key, which stays in the browser
process. The result is filtered to chat models, capped, cached per profile
and server address for a few minutes (a failed fetch is never cached), and
the saved model is always in the list, so a provider that can't be reached
never leaves the menu empty.

Base URLs are normalized (`NormalizeBaseUrl`) when saved and again when
read, so an address pasted with its request path, like
`https://openrouter.ai/api/v1/chat/completions`, works anyway; rac adds
`/chat/completions` (or `/v1/messages`) itself. Saving provider settings
also runs a connection check (`CheckProviderConnection`): `GET {base}/models`
first (`GET {base}/key` for an openrouter.ai address under any provider,
since its model list is public and would pass with any key; people set it up
as Custom too), and, for servers with no model list, a one-token chat
request, so
the user learns the address or key is wrong in Settings, not from a failed
chat. A model that rejects the browser tools makes the provider's error
clear, so the chat retries once without them and says so; a model that
can't do that at all just chats as plain text.

### Page context

Chat and the agent read pages through Chromium's AnnotatedPageContent (APC),
in its actionable mode. rac needs actionable mode because only it reports
geometry and `aria-hidden`, which the hidden-text filter relies on. Chat and
the agent share one extraction helper (`rac::agent::ExtractAnnotatedPageContent`)
for that reason. Don't call the optimization guide with default options
from new code.

Things APC can't tell you, which the serializer works around or accepts:

- **Hidden text is filtered after the fact.** `display:none`,
  `visibility:hidden`, `aria-hidden`, content-hidden subtrees, transparent
  text color, tiny rendered boxes, and boxes pushed off the left edge are
  dropped. `opacity:0` text is not exposed, so it stays in, and so does text
  pushed above the page, because the boxes are viewport-relative. Don't
  describe the filter as complete.
- **The visible box is clipped to the viewport.** An empty one only means
  "not on screen now", so it orders text (on-screen first) and never hides
  it. Hiding on it once sent chat and link summaries one screen of a long
  page, and made a short first screen look like a login wall.
- **The agent's names use the same rules,** except for empty boxes, so
  offscreen elements keep their refs.
- **Heading levels are approximated** from font size. H2 and H3 look the
  same.
- **A block bigger than the page budget (8192 tokens) is dropped, not
  split.** The serializer stops at the first block that doesn't fit.
- **The content hash is a change detector.** It is not an authentication
  primitive.

Every attached page goes into the prompt as a nonce-delimited block, and the
system prompt tells the model to treat anything inside as reference material.
The nonce is fresh whenever the page changes, and `WrapPageContent` defuses
the nonce if it appears in the title, URL, origin, or body. A new caller must
wrap page text this way. Stateless providers get the page once, in the
stable prompt prefix, and unchanged follow-ups carry a reference instead of a
second copy.

### Link summaries

Hold Option over a link for 500 ms, or use "Summarize Link" in the context
menu. Only the pointer counts: Blink also reports keyboard- and
script-focused links as the link target, so the hover path needs a recent
mouse move or scroll, more recent than any key, and rac in front.
Turning AI off stops a running summary and forgets the cached ones. The page is fetched in a hidden tab in a throwaway off-the-record
profile created for that one fetch, with cookies blocked, JavaScript, images,
and plugins off, and downloads denied. This is what keeps a summary from
using the user's logins: a link to a private page gets the login wall, and
the card says so. The text goes through the same hidden-text filter and
prompt wrapping as chat, capped at 3000 tokens. Results are cached in memory
only.

### Find-in-page Ask and new tab auto-pick

- Find shows an Ask pill instead of "0/0" when there's no match and the query
  has at least three words or ends in a question mark. The prompt travels to
  the sidebar through a pending prompt on the window's panel state, which
  expires after 15 seconds. That is how a panel that isn't open yet still
  gets it.
- The new tab page decides Search or Ask on every keystroke, locally, with no
  model call (`intent.ts`). The Search path goes through
  `AutocompleteClassifier`, so the default search engine and bangs behave as
  in the address bar. It navigates only to http(s) and chrome URLs, so a
  typed `javascript:` URL never runs.

## AI off costs nothing

This is the rule that's easiest to break by accident. How it holds:

- `AiServiceFactory` returns null unless the profile is regular and
  `IsAiEnabled(prefs)` is true. It builds nothing otherwise, and everything
  AI-related hangs off the service: history, key store, the ACP service,
  and the MCP server. A fresh start with AI off creates none of them.
- The `AgentController` is created only when AI is on, browser control is on,
  and the profile is regular (`IsBrowserControlAllowed`).
- Pref listeners stay registered so that turning AI on works without a
  restart: the top bar host, the side panel entry, the pull handle, the
  Assistant action. They watch a pref and do nothing else. The visible
  parts (Chat button, handle, menu entry, native action) are created only
  while AI is on, and removed when it turns off.
- Turning AI off cancels requests, stops the agent process, closes the
  panel, and navigates open assistant tabs to the ordinary new tab page. A
  service or controller that already exists stays in memory but dormant.
- Link hover, the context-menu item, and the find bar's Ask check
  `ShouldOffer…` or `CanAskAssistant` first and return before creating
  anything.
- The agent PATH probe is lazy. Opening the model picker runs the cached
  probe once. It never starts an agent.

When you add AI code:

1. Reach it through `AiServiceFactory::GetForProfile`. Never construct
   a service yourself.
2. Create objects on first use, not at startup or window creation. If you
   need to watch a pref, watch only the pref.
3. Handle the pref turning off while your feature is running: cancel work,
   release resources, remove UI.
4. Check the regular-profile requirement.
5. Verify in a fresh profile with AI off: no AI log lines, no extra
   processes, no requests to a provider.

## ACP agents

rac talks to installed agents over the Agent Client Protocol (ACP v1, JSON-RPC
over stdio). Like [T3 Code](https://github.com/pingdotgg/t3code), it runs the
provider's official tool instead of reusing its login.

### How they run

- rac finds the executable once, lazily, through the user's login-shell PATH,
  and caches the result. An absolute path override per agent is validated on
  a blocking-allowed thread.
- The process starts on a dedicated IO thread (file descriptor watchers
  can't run on the thread pool), in its own process group. Ending a run
  kills the group.
- The working directory is an empty scratch folder under
  `Cache/rac-agent/scratch/<agent>`. The environment starts empty: only the
  user's identity, locale, proxy, and CA settings carry over, so a browser
  started from a terminal doesn't hand its shell's API keys to the agent.
  Telemetry and auto-update are turned off where the agent has a switch.
- `initialize` advertises no file reads, no file writes, and no terminal.
  Anything else the agent asks for gets a "method not supported" reply.
- Codex and Claude run through npx adapters, pinned to exact versions. They
  need Node.js. A path override applies to the underlying CLI, not to npx.
- The recipe for each agent (`agent_recipes.cc`) removes shell, file, and web
  tools with that agent's own config. These restrictions differ by agent and
  change as agents change. Treat them as a second layer. The permission rule
  below is the one that must hold.

### Runs

A run is one prompt, and nothing of it outlives it. `AcpService::Prompt`
launches the agent, starts the MCP server, and sends the prompt. When the
prompt ends for any reason (done, an error, a sign-in request, Stop, a newer
run, AI off) the run stops the MCP server, kills the agent, and deletes its
tool provider. Every message therefore starts the agent again; there is no
idle agent between messages.

- **The run owns its tools.** The page hands `Prompt` the run's
  `AgentMcpTools`. Nothing else keeps a pointer to them, and the MCP server
  is stopped before they are deleted. A provider owned by the page once
  outlived the server's raw pointer to it, and a `tools/list` on the old
  socket crashed the browser.
- **Every stage checks its run id.** The PATH probe, the launch preparation
  on the thread pool, the MCP server's start, the agent's replies, and its
  exit all carry the run id and do nothing once it is not the current run.
  Stop during a launch therefore sends nothing, not even the page text in
  the prompt.
- **A page stops only its own run.** `Stop(run)` ignores an older id.

### Permission rule

Agents ask permission through `session/request_permission`. rac allows a
request only when `IsApprovedRacMcpTool` says it is a tool from rac's own MCP
server (server name `rac`). Everything else gets the reject option, and if
the agent offered no reject option, the turn is cancelled.

The check trusts only fields that the agent's own runtime sets, never the
title or the tool's arguments, because the model writes those. For Codex an
ordinary shell request's title is the command text, and any tool's raw input
can carry an extra `"server": "rac"`. The check is per agent and needs the
tool name to match one rac currently advertises exactly (not a prefix), and
only while rac's MCP server is running:

- **Claude:** `_meta.claudeCode.mcpServer.name` is `rac`, and
  `_meta.claudeCode.toolName` is exactly `mcp__rac__<tool>`.
- **Codex:** `_meta.is_mcp_tool_call` plus the `rawInput.server` and
  `rawInput.tool` envelope that the adapter builds around the model's
  arguments. Codex sends sparse permission requests, so the client first
  merges in the earlier `tool_call` update.
- **Everyone else** (Cursor, Gemini, OpenCode, Copilot, Goose, custom): no
  verified runtime identity, so nothing is auto-approved. Cursor doesn't
  need it, because its own `Mcp(rac:*)` allowlist calls rac's tools without
  asking. The other agents may not be able to use rac's tools until their
  identity fields are verified and added.

To support a new agent, find a field its adapter sets from the MCP runtime
(in the adapter's source, not only in a log) and add a positive test plus
adversarial ones to `AgentRecipesTest`.

Allowing a rac tool means only "this tool may be called." Whether a given
call is allowed is decided later, by the guard.

### The rac MCP server

Agents get rac's tools through an MCP server, so one agent-facing surface
serves every agent.

- It is a Unix socket at `<profile>/rac-agent-mcp/<token>/s`. The directory
  is mode 0700 and the socket 0600. When that path is longer than Darwin's
  103-byte limit for socket paths, the directory is `/tmp/rac-mcp-<uid>-<token>/`
  instead.
- Agents reach it with `/usr/bin/nc -U <socket>`, which ACP's stdio
  `mcpServers` entry can describe without shipping a helper binary. `nc`
  can't send headers, so there is no secret: the path shows in `ps`. The
  modes and a same-user-ID check keep other users out. Any process of the
  same user can connect while a run is live; it gets only that run's tools,
  through the same guard and cards.
- It lives exactly as long as its run (see [Runs](#runs)). Start and stop
  are asynchronous. Never wait for them on the UI thread: a synchronous
  join DCHECKs there. Before each start it deletes leftover directories
  whose socket no longer answers.
- It has no approval hook of its own. All real authorization is in
  `AgentController::HandleToolCall`. Don't add policy at the MCP layer, and
  don't route calls around the controller.
- With browser control off, incognito, or AI off, no tool provider is set, so
  the agent sees an empty server list. The `--rac-agent-mcp-echo` switch
  adds a harmless `rac_echo` tool for testing.

## The agent

"Agent" in rac means browser control: the assistant clicks, types, and
opens tabs. It runs in two ways, with the same tools and the same gates.

- **Direct provider.** rac runs the tool loop itself (OpenAI-style and
  Anthropic-style tool streaming).
- **ACP agent.** The agent calls the tools over MCP. `AgentMcpTools` turns
  each call into `HandleToolCall(..., kMcp)`.

Both enter the same `AgentController`. There is one active turn per
profile, owned by the assistant page that sent it (`SetAgentRunOwner`).
Only the owner shows the turn's cards and marks its tab, and only the owner
stops it, so closing a new tab page can't stop the sidebar's task. With
browser control on, every send starts a turn, so a send from another page,
even a plain question on the new tab page, ends the running task. The page
that loses it says "Stopped because another assistant page started a
task.", whether either side is an ACP agent or a direct provider:
`ClaimAgentTurn` marks the handoff in the hub and cancels the old turn while
its page still owns it. A closing page stops its run before it stops
listening; the ring and pill are taken down by that page's handler.

### Who may act

All three must be true, and are checked again before each action:
AI on, `rac.ai.browser_control` on (default true, "Let AI use the browser"),
and a regular profile. Changing either pref cancels the turn and clears the
controller's state. Every call needs an active turn, and action tools are
listed only while one is active.

The agent acts only in tabs the user attached (the current tab, when the
user chose to attach it) and tabs the agent opened. It can't close a tab the
user opened.

### Snapshot and refs

The agent sees the page as accessibility-style lines, for example
`- button "Sign in" [ref=e6] [submit]`, built from the same APC extraction as
chat and wrapped as untrusted page text.

- A ref (`eN`) is keyed on the tab, the document, and the DOM node. Numbers
  are never reused, even after the page changes. A ref from a replaced
  document fails with `stale_ref`.
- Password and payment values are shown as `[redacted]`.
- A later snapshot of an unchanged URL may be a delta. `full:true` asks for
  absolute lines with offscreen elements. The first snapshot of each turn is
  absolute.
- **Published versus private.** Before it acts, the controller takes a fresh
  private snapshot to validate the target. Only a snapshot returned to the
  model counts as published. A ref's approval is tied to its last published
  semantics, and a link's URL counts as seen only if the model was shown it.
  Without this split, a page could change a link's `href` between the model's
  snapshot and its click, and the private refresh would quietly approve the
  new destination.

### Tools and the action runner

Read tools: `snapshot`, `get_page_text`, `list_tabs`, `find_in_page`. Action
tools: `click`, `type`, `select_option`, `press_key`, `scroll`, `navigate`,
`go_back`, `open_tab`, `switch_tab`, `close_tab`, `wait_for_settle`.

The runner uses Chromium's actor framework: renderer actor tools, called
through `ChromeRenderFrame`. It does not use Glic's execution engine. rac
turns on `kGlicActorToctouValidation` by default with a one-line patch, so
every tool request is checked against the node and document it was approved
for. rac adds its own checks in the renderer (`semantic_validator`), reached
through a rac-owned Mojo interface that is requested only for agent
snapshots, so ordinary page reading is unchanged.

After an action, the runner waits for the page to settle (Chromium's page
settled monitor, 4 second cap) and returns a fresh snapshot. A model-supplied
"confirmed" argument does not exist and would be ignored. Approval comes
only from the card.

### The guard

`ActionGuard::Evaluate` decides plan, confirm, allow, or block for every
action before `ActionRunner::Run`. `Dispatch` evaluates it again for blocks
just before running.

**Block** (nothing overrides it): an unknown tool, closing a tab the user
opened, a download, a URL that
isn't http(s), or a URL that did not come from a user message or a link in a
snapshot the model was shown. The URL match is exact. `chrome:`, `file:`,
`data:`, `javascript:`, and extension URLs are never allowed.

**Always consequential**, and so always a confirmation even after the plan
was allowed:

- any native submit control, including image inputs, whatever its label says
- pressing Enter in a field
- password and payment fields, and file inputs
- words like buy, send, delete, sign in
- a target the guard can't classify (a generic click target, a text box with
  no known purpose, a select), because the critic has no page text to judge
  it
- typing text that isn't in the user's messages, in any field, since the
  critic never sees the text
- any origin outside the ones the plan allowed

**Plan.** The first action of a turn shows a plan card with the next step
and the sites involved. It is not an invented multi-step plan. Allowing it
adds those origins to the turn. It lets low-risk steps run on those sites.
It never covers a consequential step.

**Confirm.** One card per consequential action, no default button, no
keyboard shortcut for Confirm. Esc stops the turn. The card's detail text is
generic ("Clicks Place order. It sends the form to host:port") and never
includes typed text.

An approval is for the exact thing the user saw. At approval time, rac
records the element's identity, its target URL, and for a form control the
effective submission: action, method, target, and which control submits
(including a `formaction` override and the implicit submitter for Enter).
It re-checks that record at each boundary where page script can run: before
the mouse goes down, before it is released, between key events while typing,
and after the user answers. A mismatch gives `stale_ref` and the action does
not happen. Typing that would need Chromium's paste fallback fails instead,
because that path runs page events with nothing re-checked in between.

The re-read after an answer carries "this was approved" as an argument of
that one read, and Stop, a new tool call, and a new turn clear every piece
of approval state. A member flag that survived Stop once let a later click
on the same ref skip both the plan card and the confirmation.

### Containment

While an agent action is live, its tab carries an `ActionContext`. Small
hooks in Chromium's navigation, download, popup, and file picker code ask it
before allowing anything. A navigation is allowed only to an approved origin
(exact origin, including port) and, for an approved link or form, to the
approved URL, method, and target frame. Popups, downloads, and file pickers
are refused.

The traps here:

- **The exact binding is for the first request only.** By the time a
  redirect arrives, the approved request has reached the server: a form's
  POST has already placed the order. So a redirect is checked by site (an
  approved origin, or the same site as one), which lets http-to-https,
  `www.`, trailing slashes, and Post/Redirect/Get through. A redirect to
  another site is still refused, and after a POST the model is told the
  form was sent. Checking redirects against the exact URL and method once
  cancelled every such result page after the action had happened.
- **The agent's own `go_back` is not the user's.** History navigations
  from the browser look like a user pressing Back, so `TabTools::GoBack`
  marks its navigation, and the back target's origin goes on the card and
  into containment.

- **Stopping the agent does not lift containment.** A click can schedule a
  timer or a delayed download. Pause, Stop, the end of a turn, and turning AI
  or browser control off take away the agent's authority but keep the
  restrictions on every document the agent touched, including documents in
  the back/forward cache. Only a real user action hands the page back:
  trusted input attributed through native event timestamps, or a
  browser-initiated navigation. A page's own user-gesture flag is not
  evidence.
- **Cancel must not click.** Canceling a held mouse button clears the native
  mouse state. It never sends a normal release, which could activate a link
  after the guard has gone.
- **Callbacks carry a generation number.** Every renderer, settle, and
  extraction callback captures the action generation and the document, and
  is dropped if either changed. Without it, a late reply from a canceled
  action can finish the next one.

This is input and navigation containment. It is not a sandbox: script on an
approved page can still make network requests, and rac can't undo script
that ran on an input event the user approved.

### The critic

A low-risk step that the plan allowed goes to a fast safety check first. It
runs on the user's direct provider and can only say `allow` or `escalate`.

- **It never sees the page.** Its input is the user's goal (capped at 4000
  bytes), the tool name, a role from a fixed list, the numeric control type,
  canonical origins, and a few booleans. No labels, names, URL paths, or
  text. A hostile label can't talk to it, because it never arrives.
- **It fails closed.** A reply that isn't exactly a valid `allow` or
  `escalate`, a reply over 4096 bytes, a provider error, or no answer within
  4 seconds all become a confirmation card with a note.
- **No direct provider means no critic.** Every action then gets a
  confirmation, and the card says no fast model is set up.
- Consequential steps skip the critic and go straight to a card.

### Pause, Stop, and the step cap

- **Pause on user input.** Real input in the agent's tab (not synthetic
  events the agent sent) pauses the turn. A pause cancels an action that
  is already running, and the model is told it was cancelled. Nothing
  retries it unless the model asks again. Resume works from the sidebar, the
  tab pill, and the keyboard.
- **Stop** is the sidebar button, the pill, ⌘., or Esc on a card. It
  cancels the model session and, for an ACP agent, kills the process.
  Nothing continues afterward. All of them end in `AgentController::Cancel`,
  whose `stopped` event makes the owning page stop its chat session or ACP
  run.
- **Step cap.** A turn stops after 25 tool calls (`kMaxToolCallsPerTurn`,
  shared by the direct loop and the controller). The user can send another
  message to continue.

## The UI contract

The controller and the sidebar talk through events, and the sidebar has
exactly one parser.

- The controller builds events with the functions in `agent_events.cc` and
  sends them through `DispatchAgentEvent`. The page handler forwards them,
  as the `racAiAgentEvent` WebUI listener, only to a page that has a reply
  running.
- `agent_events.ts` is the only place that reads event fields
  (`parseAgentEvent`). It drops anything malformed and caps every string.
  To add an event, add a builder, a case in `parseAgentEvent`, and a case in
  `applyEvent`. Nothing else should look inside an event.
- Events: `step_started`, `step_finished`, `plan_request`, `confirm_request`,
  `paused`, `resumed`, `run_state` (working, paused, waiting, done, stopped,
  error), and `summary`. A `confirm_request` carries a `risk` (for example
  `sensitive_field`, `purchase`, `submit`, `cross_origin`, `critic`) and, when
  the critic held the step, its note. A `summary` counts `steps`,
  `confirmed`, and `failed`. A turn whose actions all failed ends in
  `error` ("Couldn't finish"), so the footer never says "Done" when
  nothing worked.
- Labels, tab titles, origins, errors, and critic notes come from pages or
  the model. Render them as plain text only.
- Decisions go back with `racAiAgentRespond(id, decision)`. There are two
  spellings: the cards say `allow`, `confirm`, `skip`, `stop`, and the
  controller says `allow_once` and `deny`. Both are accepted at the bridge
  and anything else is ignored, as is a stale ID. A bridge that accepted only
  one set once dropped every approval silently.
- ACP agents' own progress (thoughts, tool calls, plans) arrives separately
  as `rac-ai-agent-update`, which is raw ACP passthrough rendered as
  collapsed step rows. Don't confuse the two. Browser steps from rac's own
  events replace the agent's matching tool rows so one step doesn't show
  twice.

### Tab indicator

A ring on the page card and a pill with Resume and Stop mark the tab the
agent is using. Nothing exists until the first `Show`. Then a per-tab
controller watches visibility and the card's bounds, and takes the views out
while the tab is hidden. The controller drives it through `AgentTabStatus`
(working, waiting, paused, hidden), and the sidebar page handler applies it
to the right window. The views must be inserted before the capture border in
`ContentsContainerView`, which DCHECKs that it stays last. Detaching them
synchronously during a window visibility change crashes Views, so the
detach is posted.

## Debugging and testing

- `--rac-agent-debug` enables `racAiAgentDebug` on `chrome://rac-ai`:
  attach a tab, take a snapshot, click, type, select, or navigate by ref or
  URL, without a model. It also enables `racAiAgentDebugEvent`, which fakes
  agent events so the cards and indicator can be driven by hand. Both are
  off without the switch.
- Send each `chrome.send` message from the page that owns it. An unhandled
  message is a `NOTREACHED`, and it takes the browser down. Settings messages
  belong to a settings page, and assistant messages belong to the sidebar.
- `--rac-agent-mcp-echo` serves the `rac_echo` tool. Run `nc -U` against
  the socket in the profile to check the protocol by hand.
- Direct providers: point the Custom provider at any local
  OpenAI-compatible server. `http://localhost` is allowed (other `http`
  hosts, including LAN addresses, are not). Custom always asks for a key;
  any value works for a server that ignores it. For the agent
  loop the server must stream tool calls. For link summaries and the critic
  it only needs plain replies.
- ACP: pick "Custom ACP command" and give an absolute path to a script that
  speaks ACP v1 on stdio. Quote a path with spaces (`'/My Tools/agent'
  --acp`). Single quotes, double quotes, and backslashes work as in a
  shell, except that a backslash escapes any character inside double
  quotes; there is no other shell syntax. `AcpServiceTest` has a small one in shell. rac's own mock
  servers are not in the repo.
- Unit tests: `rac_ai_unittests` and `rac_agent_unittests`. Run only those,
  not Chromium's suites.

## Open concerns

- **Page script after an approval.** The guard controls input, navigation,
  popups, downloads, and pickers. It does not control what an approved
  page's own script does with the click.
- **Agents without a trusted identity.** Gemini, OpenCode, Copilot, and
  Goose permission requests for rac's tools are rejected, because none of
  their verified fields proves the call came from rac's MCP server. Add each
  one as its adapter's identity fields are verified.
- **Provider terms.** Whether a provider lets its subscription run through
  another app is that provider's call, and it can change. rac runs the
  official tool, not a reused login, and shouldn't depend on any one
  provider.
- **Setup.** Installing a CLI, installing Node.js for the Codex and Claude
  adapters, and signing in are fine for developers and hard for everyone
  else. Own keys and local models are easier.
- **Speed.** Starting an agent is slow, so small features (summaries, the new
  tab choice, Ask, the critic) go through direct providers. The critic uses
  the user's own direct model. There is no dedicated fast model, so a slow
  provider slows every low-risk step.
- **Agents report no models or modes yet.** The picker shows an agent as one
  row. Add per-agent models when ACP exposes them.
- **Rough edges in the tools.** `press_key` is Enter on an element only, and
  the guard always treats it as a possible submit. Forms that target a named window
  or a new window are denied. The agent can't close the user's own tabs. A
  new turn does not keep the agent's tab ownership from the last one.

## Prior art to study

| Project | License | Worth studying |
| --- | --- | --- |
| [ego lite](https://github.com/citrolabs/ego-lite) | MIT (agent tooling only; the browser is a separate download) | A separate space for each agent; agents write one script instead of calling tools one at a time; high-quality page snapshots; reusable skills |
| [BrowserOS](https://github.com/browseros-ai/BrowserOS) | AGPL-3.0 | A Chromium fork with an agent in the new tab and side panel; your own key or Ollama; MCP control by outside agents; session replay |
| [browser-use](https://github.com/browser-use/browser-use) | MIT | Turning pages into AI input; the agent's action loop |
| [agent-browser](https://github.com/vercel-labs/agent-browser) | Apache-2.0 | A compact page snapshot format |
| [T3 Code](https://github.com/pingdotgg/t3code) | MIT | Running Claude Code, Codex, Cursor, and others under the user's own subscription; one adapter per provider |

License notes: rac is GPL-3.0. MIT and Apache-2.0 code can be used with
credit. AGPL-3.0 code can be combined with GPL-3.0 code, but anything copied
from it keeps the AGPL's extra network requirement. Reimplementing ideas
after reading the code carries no license obligations.

## Not built yet

Scheduled and triggered automations, 1Password sign-in, a wallet, letting
outside agents (not started by rac) use the browser tools, and cloud agents.
Don't design these from this page. Ask the maintainer.
