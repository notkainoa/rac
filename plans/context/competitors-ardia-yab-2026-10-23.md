# rac vs Ardia vs Yab (2026-10-23)

> Text extracted from an HTML page rendered in the maintainer's planning thread. Not committed to main before. Treat as context, not as decided.

61days left
Arc shuts down on December 22. The Browser Company announced it today and stopped new Arc accounts. All three projects are aiming at the same wave of Arc users, and those users will pick a new browser in the next two months.
 rac
Calm Arc on Chromium, AI optional
  EngineChromium 154 via HeliumUIChrome's Views, patchedSourceOpen, GPL-3.0AIOff by default; assistant + agentPhones homeNothingShipped0 releasesWho1 person + agents
 Ardia
Dia clone with Arc's sidebar, no AI
  EngineChromium 155, ungoogledUIReact NativeSourceOpen, Apache-2.0AINone, by choicePhones homeCounted update checksShipped70 releasesWho1 person + agents
 Yab
Arc with your own Claude or ChatGPT doing the work
  EnginemacOS's WebKitUISwift, AppKit + SwiftUISourceClosed (free)AIThe headline; agent in Auto by defaultPhones homeDaily active ID, opt-outShipped35 minor versionsWhoSerafim Korablev (21st.dev CEO)
 Where each one sits
 My placement, not a measurement. Across: how central AI is to the product. Up: how open and private it is by default (source, accounts, what's sent home).
 The top-middle spot (open source, nothing sent home, Chromium, AI there when you want it) is rac's alone. Yab's spot (AI-first, closed) is next to Dia's. Ardia's is next to Helium's.
 Release pace since September 25
 Cumulative public releases. Ardia's are git tags, stable and nightly. Yab's are minor versions from its changelog, since its point releases aren't published, so its real count is higher.
 racArdiaYab
 The agent: rac vs Yab
 Ardia has no AI, so this is a two-way fight. Yab built the agent as the product; rac built it as an option you turn on.
  |  |  | rac | Yab
 Features, three ways
 rac's ✓ means built in patches, not shipped. "Helium" means rac inherits it.
  |  |  | rac | Ardia | Yab
  WebKit vs Chromium
  Yab's biggest bet, and the one that's hardest to undo.
   |  |  | Yab gains | Yab pays
    | Size | 81 MB DMG, no second engine | Its site says 40 MB; the DMG is 81 MB, the app 142 MB
    | Sites | Safari-grade rendering and energy | "A site tested only in Chrome can misbehave", in its own words
    | Extensions | Chrome Web Store installs work | Through Apple's API plus a 306 KB JS shim patching about 25 missing chrome.* areas, one extension at a time
    | Mac | Live Text, translation, on-device model, passkeys come free | Needs macOS 15.4+. The engine only updates when macOS does, and Yab can't patch it
    | Video | FairPlay | "Protected video … remain unsupported" in extensions; Widevine-only sites likely fail
  Arc was Chromium. Its users' extensions and sites all worked in Chrome. That favors rac and Ardia for the switchers who care.
  What phones home
  With every setting left at its default.
   |  |  | rac | Ardia | Yab
    | Usage | ✓None | ✓Opt-in | !Daily ID + cross-device ID, opt-out
    | Crashes | ✓Cut | ✓Opt-in | ✓Opt-in, scrubbed
    | Updates | ✓GitHub only | !Counted per day | !Own server, every 4 h
    | Servers | ✓None | !ardia.dev | !Vercel, Neon, 21st's Cloudflare
    | Auditable | ✓Open source | ✓Open source | ✕Closed
  Yab's sync is end-to-end encrypted and off by default, and it's careful (passwords never shown to the agent). But you have to take its word for it.
 Where Yab is ahead of rac
  It ships. 35+ versions in 27 days, plus an iPhone beta.
  Agent breadth. Outside agents over MCP (69 tools, one-click into Claude Code and Codex), a yab CLI, handing tasks to dots, Muse and Grok Bot, background errands, scheduled routines.
  Permissions UX. Per-site Always/Never, payment thresholds, "the browser holds the yes, not the model".
  Arc parity. Peek, Small window, and an Arc import that keeps spaces.
  Breadth. Gmail client, calendar, snippets, live folders, plugin store, sync.
 Where rac is ahead of Yab
  Trust. Open source, nothing sent home, no servers. Yab is closed and counts daily users by default.
  Chromium. Every site and extension Arc users had just works. No shim.
  AI that's optional. Off by default and costs nothing off. Yab's agent defaults to Auto in your signed-in tabs.
  Any model. Local models (Ollama, LM Studio) and seven ACP agents. Yab has no local LLMs beyond Apple's.
  Conservative safety. Plan approval, then a confirm per consequential step, plus a critic.
  Not a side project. Yab is listed under its maker's "made for the fun of it" projects.
 Worth taking from Yab
  Permissions model for phase 5: per site, per action type, money thresholds, revocable.
  One-click MCP install into Claude Code and Codex, plus a CLI.
  The remote hand-off design (device-code pairing). Phase 6, but without a third-party relay.
  Peek: Arc users expect it, and both rivals have it.
  Boosts with a reviewed store. Their CSS-only boost format is a good fit for phase 5 Boosts.
 Should we give up? No. Should we ship sooner? Yes.
 They aren't building the same thing. Yab is an AI product that happens to look like Arc. Ardia is Dia without the AI. rac is the only one that's open, sends nothing home, runs on Chromium, and keeps AI optional. That's a real gap, and Arc closing makes it bigger. But spots aren't claimed by being right, they're claimed by shipping, and rac is the only one of the three with no download.
  Get a release out before December 22. Phase 4's nightly channel is the fastest route. A signed nightly with Helium's icon beats a perfect release in January.
  Pull Arc import into phase 4. Arc users are the market for the next 61 days, and both rivals already import Arc spaces. rac can import them as real spaces.
  Keep the agent's phase 3 scope tight (the worktree already running). Don't chase Yab's breadth before release; win on trust and Chromium, then pick up outside agents and permissions in phase 5.
