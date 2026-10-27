# Pomerado — digest

Source: `plans/research/pomerado.md` (2026-10-27). Evidence: a shallow clone of `github.com/Pomerado/pomerado` at `848fcda` (read with grep, sed and cat; nothing run), GitHub and npm metadata, pomerado.ai, and an AlphaSignal article. The launch tweet returned HTTP 403 and was not read. **FACT** = seen in code, docs, or an API; **CLAIM** = Pomerado's or a third party's words; **INFERENCE** = reasoning. The dossier's Verification section is authoritative.

## In plain English

Pomerado watches an AI use a website once, then saves the result as a small program. Your coding agent can call that program later like a tool, with no AI in the loop, so it is fast and cheap. The open-source part needs an OpenAI key, Node 24 and its own Chromium, and it cannot drive rac. The "self-healing" is not in the open code; it is a paid hosted feature. For rac, copy the idea of record-once, replay-without-AI. Do not bundle it.

## Key facts

**Identity.** MIT, "Pomerado AI, Inc."; YC F26 (CLAIM). Repo created 2026-10-05; about 2,644 commits in 22 days; 1,127 stars, 98 forks, 49 open issues; version 0.4.0, hundreds of canary releases; two people wrote about 2,600 commits (FACT, GitHub and npm APIs, `LICENSE`, `package.json`). Branch names and `AGENTS.md` suggest mostly AI-written under strict review (INFERENCE). 194 unit test files and 70 browser test files with fixture sites; no real-model calls in tests (FACT, `AGENTS.md`, `find`). The API moves fast: the changelog has a long "Unreleased > Breaking changes" list and sign-in recipes are already at version 8.

**Process model** (FACT, `README.md`, `docs/how-it-works.md`):

```
Coding agent (Claude Code, Codex, Cursor...)
 └─ pomerado-mcp mint --root <dir>        Node 24.21+ MCP stdio server
     tools: mint, get_job, provide_input, cancel_job
     ├─ Minter (OpenAI gpt-6.1-sol)  writes JS "operation modules", runs them live
     ├─ Guardian (OpenAI gpt-6-luna) reviews each browser call, question, final source
     └─ Playwright-launched Chromium (its own, headless, fresh context)
Saved integration = a folder you own:
  src/  pomerado.json  auth-fill.json  deployment.json  mcp.mjs
  runs as its own MCP server, no model call, no key
```

**How a site becomes an integration** (FACT). Four stages: explore, complete one example, generalize, serve as an MCP tool. A read mint writes its own live tests and needs 70% passing before review. Authority is fixed at mint time as `read` or `write`; the agent is told to ask the user before `write`. Each mint has 20 minutes of active work. Inputs and outputs are schema-validated; failed writes return `possible_commit` so callers read back before retrying.

**Self-healing** (the key finding).
- CLAIM: pomerado.ai says it "catches the break, repairs the integration and finishes the call"; the demo patched a moved date filter in about four minutes. AlphaSignal repeats it without any mechanism.
- FACT: the open repo does not do it. The README lists "Breakage detection ... and repairs the integration automatically" under what **Pomerado Cloud adds**. `typescript/src/hosted-features.ts` lists "Maintenance and repair" as a feature the local host does not supply; `mint-host.ts` says the local host "keeps no write maintenance". The CLI has only `mint` and `run`.
- INFERENCE: mechanically, repair is a model re-running the minting loop against a stored checkpoint, reviewed by Guardian. Deterministic replay is real; healing is not.

**Browser.** Playwright launches its own Chromium, or attaches by `chromium.connect()` to a Playwright server. A plain Chromium debugging URL "won't work", and the local host "doesn't attach over CDP, since its runs close other tabs and reset site data" (FACT). So Pomerado cannot drive rac. Each run starts with no cookies; sign-in is replayed per call.

**Models** (FACT). `gpt-6.1-sol` and `gpt-6-luna` are hardcoded in `typescript/src/models/models.ts`. `OPENAI_API_KEY` is required to mint. The agent that calls Pomerado can be any model. I found no base-URL or provider setting. Prompts use OpenAI-specific cache breakpoints and compaction (INFERENCE: local models would not work). Running an integration makes no model call.

**What leaves the machine.** During a mint: task text, page observations, generated source and review evidence go to OpenAI (FACT for the flow; page content from signed-in sites is INFERENCE). Passwords typed in chat pass through the user's agent and its provider (FACT, `docs/getting-started.md`). At run time: only the target site and its sign-in origins.

**Telemetry and accounts** (FACT). No account is needed. No analytics dependency in `package.json` or the lockfile; the sign-in telemetry hook is "set none" for the local host. Not checked on the wire. Pomerado Cloud (hosted fleet, saved logins, proxies, access control) is a separate paid product: Free 100 calls/day, Premium $50/month (CLAIM).

**Security.**
- Credentials are typed only on the target origin or declared sign-in origins; forms posting elsewhere are refused. The README admits it does not check where page scripts send typed values.
- Saved logins and saved browser profiles are Cloud-only, so the open build re-asks for the password on each call.
- Prompt injection: instructions call website text untrusted data, and Guardian ignores content that tries to redefine policy. Both are model-based; I saw no red-team suite. The real defense is architectural: after minting, no model reads the page.
- **No sandbox.** Generated JavaScript runs with the user's file and network access. Docs: "Guardian review and file checks are not an operating system sandbox." Edits to `src/` or `deployment.json` are not reviewed.

**Claimed numbers** (CLAIM). About 2-4x faster, 10-1,000x cheaper, 30% more reliable on 30 tasks across 25 apps. Company-reported and unverified.

## What rac should take

Ranked. Costs: **S** days, **M** 1-3 weeks, **L** a month or more for one thread (INFERENCE).

1. **Native recipes (L).** After a good agent run, "Save as recipe" stores the successful tool calls as a short JSON list: navigate, click or type by role and name, and a check that must pass. Replay runs the same tool runner with no model. A recipe is data, so the user can read, edit and delete it, and there is no arbitrary generated code. Keep it in the profile, store no credentials (type steps ask or use the password manager), and send every replay through the guard so risky actions still ask. Recording needs the agent; replay can run with AI off. Open choices: locators that survive (rac's refs do not), how recipes take inputs, and whether a failed replay stops or offers the agent a repair that the user approves as a diff.
2. **Outside-agent access, generic (M).** Already item 1 in the Aside digest: a separate switch, a 0600 Unix socket, calls routed through the guard, no raw REPL or CDP. A recipe runner can later appear there as a `run_recipe` tool. This is not for Pomerado specifically, since it cannot attach to rac.
3. **Ignore it for the product, but try it yourself (S).** MIT and installable with `npx`; the maintainer can use it with their own coding agents. It costs rac nothing. It needs an OpenAI key and sends page content to OpenAI during a mint.
4. **Embed or bundle it (last).** See "avoid".

Small borrowable ideas (S each): authority fixed at record time; declared questions only (a run may ask only what was reviewed at save); `possible_commit` on failed writes; credentials only on declared origins; fresh context for unattended replays.

## What rac should avoid

- **Embedding.** Fails all three non-negotiables: private (OpenAI key, page content to OpenAI), AI off costs nothing (a second Node 24 and Playwright runtime), cheap to update (breaking changes daily on a three-week-old 0.x API, while rac is already seven Helium releases behind).
- **Generated JavaScript as the saved artifact**, run unsandboxed at user privileges. Use data steps.
- **A hardcoded model vendor.** rac's providers are API key, local, or ACP.
- **A second Chromium.** Nothing in it would reuse rac's guard, confirm cards, permission levels, or the user's sessions.
- **Promising "self-healing" before it exists.** Pomerado's open build does not have it either.

## Caveats

- The tweet was unreadable (403), so the announcement text and the author's role are unknown. The tweet author `akshay_manglik` is likely the contributor `AkshayM21` (INFERENCE).
- Nothing was run: no install, build, tests, or network capture. "No telemetry" means none found in code.
- Did not trace whether the minter ever sees a raw password, or whether `OPENAI_BASE_URL` would work. Local-model unsupported is INFERENCE.
- Did not read the hosted product's code; how Cloud repairs sites is unknown.
- Recipe design (locators, inputs, repair flow) is open and for the agent-design thread.

## Where to look in the full dossier

- `## Architecture` — process model, minting stages, self-healing, hosted-only list, browser.
- `## Models, accounts, telemetry` — model IDs, egress, telemetry.
- `## License and maturity` — repo age, commits, contributors, tests.
- `## Security` — credentials, injection, no sandbox.
- `## Fit with rac's non-negotiables` — comparison table.
- `## Options for rac, ranked` — the four options with reasoning.
- `## Verification` — checked in code versus marketing versus not checked.
