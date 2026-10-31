# AI off costs nothing: set 1

Checks for plan 05, "Proving AI off costs nothing", items 2 to 6, on a fresh
profile with AI off. Item 1 (no `AiService`, no `AgentController`) is a unit
test, not a check here. Set 2 (the door on, AI off) is not built.

Nothing here has touched a real build. The checks are tested on fabricated
input. The browser-facing part of `run_ai_off.py` is marked `TODO(binary)` and
has never run.

## What each check proves

| Item | Function | Fails when |
| --- | --- | --- |
| 2 | `check_no_mcp_dir` | `<profile>/rac-agent-mcp` exists (even empty: the server creates it before listening), or a new `/tmp/rac-mcp-<uid>-*` appeared (the long-path fallback). |
| 2 | `check_no_agent_sockets` | A unix socket of the browser or its children sits inside the profile, or its path contains `rac-mcp` or `rac-agent`. Anonymous socketpairs and Chromium's `SingletonSocket` are fine. |
| 3 | `check_process_tree` | A descendant of the browser is not a Chromium helper from inside the app bundle (gpu, renderer, an allow-listed utility, or the crashpad handler). `node`, `npx`, `claude`, `codex`, `nc` and the rest fail by name. |
| 4 | `check_no_provider_requests` | The fake model logged any request, or the net-log has a `URL_REQUEST_START_JOB` with the `rac_ai_chat` or `rac_ai_models` annotation hash, or any event names the fake model's host:port. The profile is seeded so a stray request lands on the fake model. |
| 5 | `find_forbidden_labels`, `surfaces.check_text` | A surface other than `settings-assistant` shows Assistant, Ask AI, Ask, AI, Chat, Summarize, Agent, and so on. Whole words only. |
| 6 | `compare_states`, `set_ai_enabled` | After AI is turned on and off there is a new kind of process, a new socket path, a new MCP directory, or more provider requests than before; or either `setPref` toggle didn't take (a silent failure would compare "never on" with "still off"). |

Turning AI off leaves an existing service in memory, dormant (ai.md), so item
6 only compares what can be observed. Children are compared by name, not
count: Chromium may add another renderer for a page opened in between.

## Run it

From `devutils/rac/evals`:

    python3 ai_off/run_ai_off.py --self-test    # also --dry-run; no browser, no network
    python3 ai_off/run_ai_off.py --plan         # the steps of a real run
    python3 -m unittest discover -s . -t . -p 'test_*.py' -v

`--self-test` exits 0 only if every check passes healthy input and flags
unhealthy input.

A real run (`python3 ai_off/run_ai_off.py [--bundle PATH] [--keep-profile]`)
needs a built worktree. It refuses any profile that isn't
`<repo>/build/rac-evals-*` or under the system temp dir. Don't run it
without the maintainer's go-ahead: it launches rac.

## Surfaces

`surfaces.json` lists 27 surfaces with plain-language steps and what must not
show. `surfaces.plan_outputs(surfaces, dir)` gives each a numbered PNG path
and the `--rac-window-screenshot=<path>` flag (rac writes its own window after
the first paint; `screencapture -l` of another app is blank on macOS 26).
WebUI surfaces (`capture: devtools+screenshot`) can also be read through
DevTools with `surfaces.PAGE_TEXT_JS` and checked with `surfaces.check_text`.
`run_ai_off.py` does that part, on 6 of the 27 surfaces (`new-tab-page`,
`new-tab-typed-query`, `rac-ai-page`, `settings-main`, `settings-privacy`,
`settings-assistant`). The other 21 — native surfaces (menus, context menus,
the pull handle, sidebar states) — need the screenshot and a person or a Cua
driver to compare it with `must_not_show`; that driver is not written. The
run's summary prints both lists, so the report never implies all 27 were
checked.

## The traffic annotation hash

`checks.traffic_annotation_hash` is `net::internal::ComputeAnnotationHash` from
`net/traffic_annotation/network_traffic_annotation.h`
(`ret = (ret * 31 + char) % 138003713`), not `base::PersistentHash`. It
reproduces every reference value in
`tools/traffic_annotation/scripts/auditor/auditor_test.py`. It has not been
compared with an event from a real rac net-log, so the check also flags any
event that mentions the fake model's host:port.

## Still needed from a binary, and what is guessed

Each is marked `TODO(binary)` in the code.

1. **Baseline processes.** `BASELINE_PROCESS_TYPES` and
   `BASELINE_UTILITY_SUBTYPES` are written from memory of Chromium. Run once
   with AI off, read `ps`, and make the list match. `on_device_model` is left
   out on purpose.
2. **`ps` and `lsof` formats.** `parse_ps` assumes the executable ends at the
   first ` -`. `parse_lsof_unix` assumes NODE is blank on macOS and that
   spaces in COMMAND come as `\x20` or plain spaces.
3. **Bundle path.** `find_bundle` takes the first `.app` in
   `build/src/out/Default`. Pass `--bundle` otherwise.
4. **The launch goes through `run.launch_args`**: the app binary itself
   (`build/src/out/Default/rac.app/Contents/MacOS/rac`), wrapped in
   `build-queue.sh --run` unless `RAC_EVALS_NO_QUEUE=1`, with the net-log
   flags appended (`--log-net-log`, `--net-log-capture-mode`). The browser
   process is found by its `--user-data-dir=<profile>` (the queue doesn't
   exec the browser, so the pid `Popen` returns is not used).
5. **Pref names** in `seed_preferences`: `rac.ai.enabled`,
   `rac.ai.provider`, `rac.ai.provider_settings.custom.base_url`,
   `rac.ai.browser_control`, `rac.ai.agent_permission_level`, and
   `helium.services.enabled` (off, so a throwaway profile never reaches
   Helium's services).
6. **Toggling AI** with `chrome.settingsPrivate.setPref('rac.ai.enabled', ...)`
   on `chrome://settings`. It needs that pref in the settings-private
   allow-list. If it isn't, click the switch on `chrome://settings/assistant`.
7. **Net-log.** `--log-net-log` writes the file only at close, so the browser
   must exit through `Browser.close`. The event params (`url`,
   `traffic_annotation`) are from `net_log_event_type_list.h`.
8. **Surfaces.** Every `how` is a guess: the command bar shortcut, the layout
   switch for the toolbar address bar, the right-edge hover, the onboarding
   flag (`--force-first-run`), and which strings Settings > Privacy has.
   `BENIGN_PHRASES` ("Ask websites not to track you" and two more) are stock
   Chromium strings that contain a forbidden word; extend them from the real
   pages. A page that shows AI words only inside `settings-assistant` is the
   rule; if Settings search results or the sidebar of Settings show them,
   that is a finding, not a false positive.
9. **Shared `/tmp`.** Another rac with AI on creates `/tmp/rac-mcp-*`. The run
   ignores directories that existed before launch, so a concurrent run can
   still hide a leak or fake one if started in between.
10. **`localhost`.** The fake model is reached as `localhost:PORT`. If
    Chromium logs `127.0.0.1` or `[::1]`, the host check treats them as
    equal.
