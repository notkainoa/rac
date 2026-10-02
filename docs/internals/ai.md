# AI (work in progress)

**Status: nothing on this page is a design.** rac's AI hasn't been designed
yet. This page collects the ideas and concerns raised so far so they aren't
lost. When AI work starts, it will be rethought from scratch, and this page
will be rewritten as decisions get made.

Agents: don't build AI features or design AI architecture from this page
unless the maintainer explicitly asks.

## Settled

These come from [VISION.md](../../VISION.md) and hold whatever the design
becomes:

- AI is off by default. Onboarding has a screen asking whether you want it,
  and you can turn it on or off in settings at any time.
- When AI is off, none of its code does any work: no processes, no network
  calls, no background tasks.
- rac never sees AI conversations. Only the user and their chosen provider
  do.
- No rac-hosted AI service for now.
- The agent never takes an action in the browser without the user's
  confirmation.

## Ideas so far

### Where the AI comes from

- The user's own API key (OpenAI, Anthropic, Google, OpenRouter, and so on)
- Local models (Ollama, LM Studio, or similar)
- Signing in with an existing subscription by running the provider's own
  agent, such as Claude Code, Codex, or Cursor. rac would show the agent in
  the sidebar and give it browser tools, possibly through MCP. This is
  similar to how [T3 Code](https://github.com/pingdotgg/t3code) runs coding
  agents.

### Features

- An AI sidebar on the right that can read the current page. It should be
  minimal, like Dia's, not cluttered like Aside's.
- Link hover summaries.
- A new tab box that searches the web or asks the AI, picking one
  automatically as you type.
- Cmd+F that offers an "Ask" button when a longer query isn't found on the
  page. Clicking it or pressing Enter opens the AI sidebar with that prompt.
- Calm progress display: short states like "Thinking..." and
  "Reading page..." with a nice animation. The detailed steps stay collapsed
  until you expand them.

### The agent

- Browser control: clicking, typing, and opening and managing tabs, across
  several tabs. Only when the user asks, and only after the user confirms.
- A safety checker: before each agent action, a second, fast AI compares the
  user's request, the steps so far, and the planned action. If the action
  doesn't match what the user asked for, the agent pauses and asks the user.
  Candidates mentioned so far are fast "system one" models, such as jev or
  an OpenAI decision API.
- Later: scheduled and triggered automations, 1Password sign-in, a wallet
  with 1Password cards, letting outside agents use rac's browser tools
  through MCP, and possibly cloud agents (exploring only).

## Concerns to resolve during design

- **Prompt injection.** Coding agents like Claude Code and Codex can run shell
  commands and edit files. A browser agent reads untrusted pages. If rac runs
  those agents, it probably has to remove shell and file access and give
  them only browser tools. Each provider controls this differently.
- **Speed.** Starting a coding agent is slow. Small features such as hover
  summaries, the new tab choice, Cmd+F, and the safety checker may need a
  separate fast model instead of going through an agent.
- **Setup.** Installing a command-line agent and logging in is fine for
  developers, but hard for everyday users. API keys and local models are
  easier.
- **Provider terms.** Whether a provider allows its subscription to be used
  through another app is up to that provider, and it can change. Running the
  provider's official tool is safer than reusing its login, and rac shouldn't
  depend on any single provider.

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
