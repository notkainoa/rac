# Council review: rac vs Inbox Zero (Opus)

Citation keys: **AUDIT** = `rac-audit.md` (ERRATA block applied over the body), **PROD** = `inboxzero-product.md`, **ARCH** = `inboxzero-architecture.md`, **TRAC** = `inboxzero-traction.md`. Section numbers follow each file's own headings. Text marked **[inference]** is my reasoning, not something the dossiers state.

---

## 1. Verdict in five sentences

Inbox Zero is a real business that ships. It has paying customers, a test suite that CI runs on every PR, and a working distribution machine. rac is a thoughtfully designed browser that nobody but its maintainer has ever run. On the things rac's own vision cares about most (privacy architecture, license honesty, and how deep the agent's safety mechanisms go), rac's design is ahead of Inbox Zero. Inbox Zero's "open source" label, its self-reported compliance claims, and its server-side store of email-derived content do not hold up under scrutiny. rac's lead is only on paper until it ships, though. Its default `auto` agent policy also permits a prompt-injection exfiltration chain that Inbox Zero's drafts-not-sends defaults would not allow, and rac has zero evals to measure the risk. The thing to learn from Inbox Zero is not its features or its pricing: a solo founder with AI agents stays upright through automated gates (tests on every PR, evals, PR-only main) and constant distribution, and rac has skipped both. With Arc shutting down on Dec 22, rac should stop writing agent code, sync to current Helium, ship one signed build with Arc import, and tighten the agent default; if it doesn't, the Arc window closes on a browser nobody has heard of.

---

## 2. Scorecard

Each product is scored 1–10 on its own terms. For "Upstream/platform risk", 10 means low, well-managed risk.

| Dimension | rac | Why (rac) | Inbox Zero | Why (Inbox Zero) |
|---|---|---|---|---|
| Product clarity | 6 | "Arc on Helium with optional AI" is coherent (AUDIT §6), but 57% of new code went to AI and agent work while Arc import, the command bar, and boosts don't exist (AUDIT §1), and the repo still says "Helium Browser for macOS" (AUDIT §0). | 6 | The one-liner is crisp ("AI email assistant for Gmail and Outlook", PROD §1), but it's really two products, 16 vertical landing pages, and a surface spanning bots, a meeting recorder, SCIM, and more (PROD §0.8). |
| Feature depth | 5 | Spaces, pinned tabs, the sidebar, and AI/agent are substantial in code. But fix commits outnumber feat commits 121 to 99, there are 24 `fix-*` patches, and the key Arc-refugee features are missing (AUDIT §1, §5). | 8 | A broad and deep rules engine, drafting, cleanup, chat, MCP, and clients (PROD §2). Several headline features are still "Early Access" (PROD §9.3). |
| Shipping and distribution | 1 | 0 releases, the release workflow has never succeeded, signing is configured but unproven (ERRATA), 2 unique visitors in 14 days (AUDIT §0, §5, §6). | 8 | Continuous deploy, 20 desktop releases in about 2 months, Product Hunt #1 on 2 of 3 launches, a 167-point Show HN, about 170 SEO posts, and affiliates (TRAC §1.4, §4). The changelog has been stale since Aug 2024 (PROD §8). |
| AI architecture | 6 | BYO cloud keys, local models, ACP agents, APC extraction (AUDIT §3). Built on Google's moving Glic/actor and optimization_guide internals (AUDIT §2, §7.9), and ACP cold-starts take 15–25 s per message (AUDIT §3). | 8 | One choke point (`llms/index.ts`) with tiered fallbacks, a required hardening declaration, DLP, cost accounting, and structured output across 15 providers (ARCH §5.1). |
| AI safety (prompt injection, action gating) | 5 | The mechanisms are strong: TOCTOU checks, URL provenance, containment that survives Stop, a critic that never sees page text. But the **default** `auto` level allows a cross-origin navigate → read → type → page-script exfiltration chain, and there are no evals (AUDIT §3; ERRATA). | 6 | AI output is confined to user-authored template slots and tested by a 555-line security test, chat sends are two-step, and agent tools are read-only (ARCH §5.3). On the other side: DELETE is rated "low risk", `manageInbox` scope is enforced only by the prompt, auto-send rules run unattended, the evals don't gate PRs, and the first injection case only tests the sanitizer (ARCH §5.3, §5.5). |
| Privacy and trust | 8 | Nothing goes to rac: no server, no accounts, no telemetry, AI off by default, disclosures are honest (AUDIT §4). It depends on Helium's servers with no agreement in place, Option+hover fetches pages the user never opened, and "AI off costs nothing" is unmeasured (AUDIT §3, §4). | 4 | Email content goes to LLMs by design. Derived content (digests, drafts, chat transcripts, meeting transcripts) is stored in plaintext. The client calls PostHog `identify(userEmail)`. SOC 2/CASA claims show "0 documents". The privacy policy contradicts itself, and a private build overlay means the hosted app isn't reproducible from the repo (ARCH §3, §8, §11; PROD §6). |
| Engineering quality and testing | 3 | About 284 tests that CI never compiles or runs. "Sanity" passes when its 30 s timeout expires. Seven feature groups have zero tests, and pinned tabs has one (AUDIT §5). The docs are rigorous (AUDIT "What is genuinely strong"). | 7 | About 8,700 tests, a test/source ratio of about 0.9, CI on every push and PR, emulated Playwright, and about 430 evals (ARCH §9, §5.5). Repo-wide `tsc` is "unsupported", the codebase is a 628k-line sprawl, and webhooks aren't durable (ARCH §9, §12, §4). |
| Upstream/platform risk | 2 | Two Chromium majors behind, the sync has never been done, there are 871 upstream hunks (320 in `ui/views`), it depends on Glic/actor, and Helium bans AI-written contributions (AUDIT §5, §7.2, §7.6). | 5 | Depends on the Gmail/Graph APIs, restricted scopes with annual CASA, Google's own AI inbox features as a competitor, and Vercel-first assumptions (ARCH §4, §12; TRAC §6, §5.2). The code itself is its own: no rebase tax. |
| Open-source health and license honesty | 5 | GPL-3.0 inherited from Helium and stated plainly (AUDIT §0). But it has zero contributors, stars, or issues, the repo is still a GitHub fork, and it can't upstream anything (AUDIT §0, §5). The license is honest, but there is no community. | 4 | 12.8k stars, and 66% of external PRs merged with a median of 34.6 h (TRAC §1). It markets itself as "AGPL" or "open source" while adding monetization and 5-user terms that the self-hosting docs never mention, keeps the iOS app closed, has an `ee/` commercial carve-out, and runs a private overlay (PROD §5.3; ARCH §11). There is a community, but the license framing isn't honest. |
| Business viability | 1 | No model and no stated intention of one. Users bring their own AI key, so there is no margin. It depends on paid agent capacity (AUDIT §6, §5 "Bus factor"). | 6 | Claims >$10K MRR (unverified, as of Oct 2025) and 25k sign-ups, plus TinySeed backing (TRAC §0, §2.3, §2.4). The estimate of about 400 paying seats rests on stale claims, and the platform is under threat from Google (TRAC §2.4, §6). |
| Solo-founder + AI-agent process discipline | 3 | Worktree parallelism and AGENTS.md rules are real strengths. But 70% of commits go straight to `main`, there is no branch protection, CI never builds rac code, Pullfrog has failed about 50 runs in a row, and effort runs opposite to the roadmap (AUDIT §0, §5, §7.7). | 7 | Work flows through squash-merged PRs (94% of the founder's work goes through a PR, TRAC §1.5) gated by CI, with written agent norms, supply-chain cooldowns, and a read-only Claude workflow (ARCH §1, §7, §9). The founder self-merges in a median of 0.9 h, and agent-driven breadth is turning into sprawl. |

---

## 3. Where Inbox Zero is clearly better than rac, and why it matters for rac

1. **It ships, continuously, and has done so for three years.** The hosted app deploys from `main`, and there were 20 Electron releases between 2026-08-16 and 2026-10-21 (TRAC §1.4). rac has 0 releases, and its 10-phase CI release has never finished (AUDIT §0, §5). *Why it matters:* every advantage rac has on paper is worth zero to an Arc refugee on Dec 22. The update key and feed URL can never change (AUDIT §7.1), so the first release has to be right *and* has to arrive soon. That makes it a forcing function, not something to keep postponing.

2. **Tests actually gate changes.** `test.yml` runs Biome, typechecks, custom checks, sharded unit tests, integration tests against Postgres and Redis, and desktop tests on every push and PR. Playwright also runs on PRs (ARCH §9). rac's CI only checks patch syntax and that patches apply, then "passes on timeout" after 30 s. Its 284 tests never run (AUDIT §5). *Why it matters:* both founders produce most of their code with AI agents (73% vs 96% AI-trailered, ARCH §12, AUDIT §0). Inbox Zero's founder also self-merges in under an hour (TRAC §1.5). The difference between them is not human review; it's the automated gate. rac has the same agent-heavy workflow without the gate.

3. **It measures LLM behavior, including security behavior.** It has about 431 eval cases across a model matrix, with semantic judges and dedicated prompt-security, phishing-hardening, and memory-safety evals (ARCH §5.5). rac has "no red-team suite or eval in the repo" (AUDIT §3). *Why it matters:* rac's biggest security exposure, the `auto`-level exfiltration chain, is explicitly "unmeasured" (ERRATA). Inbox Zero shows that a solo founder can maintain an eval harness.

4. **Its defaults for side effects are more conservative.** Drafts are not auto-sent. In chat, `sendEmail`/`replyEmail`/`forwardEmail` return a confirmation payload, and the send happens in a separate server action. The MCP research agent loads only read tools (ARCH §5.3; PROD §7.2). At rac's default `auto` level, cross-origin navigation and typing model-generated text into the attached tab are both `kAllow` (ERRATA; AUDIT §3). *Why it matters:* rac reaches the user's logged-in real profile, which is a larger blast radius than one mailbox. The safer default belongs in the product with more at stake. (Inbox Zero isn't clean either. Its Cold Email rule emails the sender by default, PROD §7.2, and `manageInbox` runs without confirmation, ARCH §5.3.)

5. **It has a working distribution machine.** It hit #1 of the day on Product Hunt twice, had a 167-point and 143-comment Show HN, has about 170 SEO posts, comparison pages against every competitor, a 25% lifetime affiliate program, and a 102K-subscriber YouTube channel (TRAC §4). rac's site says "Coming soon, star the repo" to 2 unique visitors, with no audience capture "by design" (AUDIT §6). *Why it matters:* the Arc shutdown is a one-time acquisition event, and rac currently has no channel to reach those users at all.

6. **One choke point for every model call.** All LLM calls go through four functions that *require* a `promptHardening` type field, enforce DLP, record cost, and log redacted prompts (ARCH §5.1). The rac audit describes several separate outbound paths (chat, link summaries, the critic, the direct-provider tool loop, ACP agents) and no equivalent single gate (AUDIT §3). Whether rac has one internally is unknown from the dossiers. *Why it matters:* rac's two strongest promises, "AI off costs nothing" and "nothing goes to rac", are much easier to verify against one choke point than against five call sites (AUDIT §3 notes the guarantee "rests on code review").

7. **The supply chain is hardened.** pnpm enforces a 24 h `minimumReleaseAge`, there's an allowlist for install scripts, CVE-driven overrides, and SHA-pinned actions in a read-only Claude workflow (ARCH §1, §7). The rac audit records only that the npx adapters are pinned to exact versions (AUDIT §3), and that Pullfrog's workflow is broken (AUDIT §5). *Why it matters:* a browser is a top-tier supply-chain target, and rac pulls in Node adapters at runtime.

8. **It follows through on the top user complaint.** The dominant objection at launch was "don't send my email to OpenAI". The founder promised local-model support, then shipped Ollama, OpenAI-compatible endpoints, and BYO keys (TRAC §5.2). *Why it matters:* rac's equivalent top ask is predictable (Arc import, AUDIT §1, §6), and rac hasn't started it.

9. **Its versioning reflects risk.** The desktop app is honestly versioned 0.1.x (PROD §2.4), and features are labeled "Early Access" (PROD §2). rac's riskiest code, the agent, sits under a roadmap phase called "optional, after release" but is fully built and enabled at `auto` (AUDIT §1, §3). *Why it matters:* rac needs a "Labs" boundary for the agent.

---

## 4. Where rac is clearly better than Inbox Zero

1. **Privacy architecture, structurally, not just in policy.** rac has no server, no accounts, no telemetry, and no site analytics (AUDIT §4). Inbox Zero stores derived email content server-side in plaintext (digests, drafts, chat transcripts including email the assistant read, meeting transcripts, LLM reasoning that paraphrases mail, ARCH §3). It identifies users to PostHog by email (ARCH §8) and loads GTM on its homepage (PROD §6). rac's design can't leak what it never collects. This advantage holds up.

2. **Local models for ordinary users.** rac supports Ollama and LM Studio in the shipped client (AUDIT §3). In Inbox Zero, local models are "possible only via self-hosting" (PROD §4), and self-hosting needs a Google Cloud project, Pub/Sub, and a public HTTPS URL (ARCH §10). This directly answers the complaint that dominated Inbox Zero's HN launch (TRAC §5.2). It holds.

3. **License honesty and reproducibility.** rac is plain GPL-3.0 and says so (AUDIT §0). Inbox Zero markets "AGPL" or "open source" while prepending field-of-use and 5-user restrictions that its self-hosting docs never mention (PROD §5.3, §9.1). Its hosted build also overlays private code (ARCH §11), which answers the HN commenter who asked whether the GitHub code is what actually runs (TRAC §5.2). [inference] rac's releases can be reproduced from the public patch stack, since the audit mentions no private overlay. It holds, though it's worth little until there is a release to reproduce.

4. **How deep the agent safety mechanisms go.** rac re-validates element identity, target URL, and form submission at each boundary where page script can run. It separates published from private refs, requires navigation targets to come from a user message or a link the model was shown, keeps containment across Stop, runs a critic that never sees page text, checks the runtime identity behind ACP permission requests, and always blocks closing the user's tabs (AUDIT §3). Inbox Zero's agents rely on prompt text for `manageInbox` scope, rate DELETE as "low", and let a user enable any custom MCP tool inside an email-driven agent (ARCH §5.3). This holds as **mechanism design only**. rac's default policy (point 4 in section 3) throws away much of the benefit.

5. **Candor about its own security gaps.** `docs/internals/ai.md` lists seven open concerns, including "script on an approved page can still fetch()" and the admitted holes in the hidden-text filter (AUDIT §3). Inbox Zero's public materials contradict themselves on retention, on whether MCP can send mail, on compliance wording, and on platform support (PROD §9). It holds for internal docs. It holds less for rac's public site, where "a thin layer on top of Helium" and "never slower than Helium" are unbacked (AUDIT §2, §4).

6. **AI off by default, and incognito excluded.** AI services return null unless AI is enabled and the profile is a regular one (AUDIT §3). Inbox Zero's whole product *is* the AI, so this is partly a category difference (see section 5). It holds as a trust posture, not as a performance claim, because no measurement backs it.

Things I considered and rejected as rac advantages: hidden-text filtering (both are admitted to be incomplete, AUDIT §3, ARCH §5.2), docs volume, and "focus". rac sprawls too: 15 patch groups before a first release (AUDIT §1).

---

## 5. The comparison's traps

1. **Continuous deploy doesn't transfer to a desktop browser with an immutable update channel.** Inbox Zero can push a fix to `main` and every user gets it (TRAC §1.4). rac's update key and feed URL can never change (AUDIT §7.1), every release is many hours to days of macOS runner time (AUDIT §5), and a bad build sits on users' machines. "Ship faster like Inbox Zero" is the wrong lesson. The right one is "ship *once*, correctly, then on a cadence."

2. **Copying "8,700 tests on every PR" isn't feasible.** Inbox Zero's tests run on Linux in minutes. rac's tests require building Chromium targets in a 100 GB tree, where a single release-workflow phase took about 4.5 h (AUDIT §5). [inference] rac's achievable gate is narrower: compile and run the five rac test targets incrementally on a cached tree, possibly nightly rather than per-PR. The principle transfers. The scale doesn't.

3. **The prompt-injection threat models differ.** In Inbox Zero, the AI mostly fills slots in actions the user wrote (ARCH §5.3 Layer 2). That's a narrow action space, and it's *why* its defaults look safe. rac's agent is open-ended: it acts in the user's logged-in profile across origins (AUDIT §3). Inbox Zero's containment pattern can't be copied wholesale. rac needs information-flow rules (what read data may be typed where), which have no analog in Inbox Zero.

4. **"Open source as a marketing cheat code" depends on a self-host story and a founder audience.** Inbox Zero's stars come from launches and a YouTube channel that predates the product (TRAC §3.4, §4.3). Self-hosting is its trust funnel. Nobody self-hosts a browser, and Arc refugees mostly aren't developers (AUDIT §6). For rac, the repo is a trust artifact, not a growth engine.

5. **Business-model envy.** Inbox Zero's margin comes from hosted AI at $20–50 per seat (PROD §5.1). rac's AI runs on the user's own key, with no accounts and no server (AUDIT §6). Any lesson that implies accounts, a hosted AI proxy, or telemetry for conversion tracking contradicts rac's first rule.

6. **Platform risk isn't the same kind of risk.** Inbox Zero's platform risk is about API *policy* (scopes, CASA, Google competition, TRAC §5.2, §6), and it owns all of its code. rac's is *code-level* merge debt every Chromium cycle, against a stack of 180 ordered patches (AUDIT §2, §5). Inbox Zero's velocity practices assume you own your codebase, so they don't account for rac's rebase tax.

7. **Commit, PR, and star counts aren't health signals for either project.** Inbox Zero's October 2026 commits were 71% AI-trailered, and its stars are launch-driven, with 45 watchers (TRAC §1.6, §8). rac's 269 commits in 12 active days come from parallel agents (AUDIT §5). Neither project should be judged on volume, and rac shouldn't chase stars.

8. **The human-review gap looks unique to rac, and it isn't.** Inbox Zero also has effectively no second human reviewer: the founder self-merges in a median of 0.9 h, and 84% of PRs are his (TRAC §1.3, §1.5). AUDIT §7.5 presents "0 human approvals" as a top-5 risk. The real difference is that Inbox Zero's self-merges pass a CI gate. Hiring a reviewer is the wrong fix. A gate is the right one.

9. **Feature breadth followed revenue at Inbox Zero, and it costs rac far more.** Each Inbox Zero feature is owned code. Each rac feature becomes upstream hunks to refresh every Chromium major, forever (AUDIT §2). Copying Inbox Zero's breadth would compound rac's worst structural risk.

---

## 6. What rac should steal, ranked

| # | Practice (Inbox Zero source) | rac adaptation | Cost to rac | Why it's worth it |
|---|---|---|---|---|
| 1 | **A CI gate on every change** (ARCH §9) | Make `main` PR-only with branch protection. Add a required job that compiles and runs `rac_ai_unittests`, `rac_agent_unittests`, `rac_spaces_unittests`, `rac_updates_unittests`, and `rac_pip_tests` against a cached tree. Replace the 30 s "sanity" pass-on-timeout with a real compile of rac's targets. | High: macOS runner hours plus cache engineering. sccache work is already in flight but unproven (AUDIT §5). If per-PR is too slow, start nightly and make it block releases. | The 96% AI-authored code currently has no automated check. It's the single fix that matters most for AUDIT risks #4 and #5. |
| 2 | **Security evals across a model matrix with semantic judges** (ARCH §5.5) | An agent injection suite: hostile pages served from a local test server, covering the four-step exfiltration chain from AUDIT §3, `opacity:0` and off-screen text (the admitted gaps), and links to logged-in origins. Run it against the providers rac supports. **Avoid Inbox Zero's mistake**: don't use payloads the sanitizer strips (ARCH §5.5). | Medium: harness work plus API spend. [inference] It can start below the browser level by feeding snapshot text to the tool loop and checking the guard decisions. | Turns the biggest "unmeasured" item (ERRATA) into a number. Needed before the agent ships to strangers. |
| 3 | **Side-effect-conservative defaults** (ARCH §5.3; PROD §7.2) | Change the default from `auto` to `careful`, or keep `auto` but require a card for (a) any navigation to an origin the user didn't name and (b) any typing after the agent has read a different origin in the same turn. | Low: a policy change plus updates to `AutoAsksOnlyForRiskAndForeignTyping` (ERRATA). There's some UX friction. | It closes the documented chain cheaply, without waiting for evals. |
| 4 | **Structural containment of what the AI can write** (ARCH §5.3 Layer 2, `choose-args.security.test.ts`) | Information-flow tagging: text the agent types carries the origins it was derived from, and typing data from origin A into origin B needs a card. Add a dedicated security test file for it, like Inbox Zero's 555-line one. | Medium: new code in rac-owned agent files, not upstream hunks (AUDIT §2 shows the agent group follows the new-file rule). | It's the durable, model-independent fix that point 3 only approximates. |
| 5 | **A single LLM choke point with a required declaration** (ARCH §5.1) | One C++ entry point for every outbound model or provider request, with a required enum for data class (page text, metadata, none) and trust level, a counter of how many requests were made, and redacted logging. Expose a test hook so a unit or browser test can assert zero calls with AI off. | Medium: refactoring rac-owned ai files. | It makes "AI off costs nothing" and "nothing goes to rac" checkable (AUDIT §3 says the guarantee rests on code review). |
| 6 | **The launch playbook** (TRAC §4.1, §4.2, §4.4) | Coordinate Show HN and Product Hunt with the first signed release. Write comparison and "Arc alternative" pages (rac vs Arc, Dia, Zen, Helium), and an "Arc is shutting down Dec 22: how to move" guide. None of it needs analytics. | Low: writing, plus one launch day. | Arc refugees are searching *now*. Inbox Zero shows SEO and comparison pages are durable, and PH and HN are repeatable for a solo founder. |
| 7 | **Supply-chain hardening** (ARCH §1, §7) | SHA-pin all GitHub Actions, give AI and review workflows read-only tokens, delete or fix Pullfrog (about 50 failed runs, AUDIT §5), and keep the npx adapter pins with a review step on version bumps. | Low. | A browser plus its release secrets (the ERRATA confirms all signing and Sparkle keys are repo secrets) make a high-value target. |
| 8 | **A public SECURITY.md with response times** (PROD §6) | Disclosure address, scope (rac's patches vs Helium vs Chromium), acknowledgement within N days, and a stated policy on Chromium security-release lag. | Trivial. | Responsible disclosure is table stakes for a browser, and it makes the sync commitment public. |
| 9 | **Honest maturity labels** (PROD §2 "Early Access") | Ship the agent behind "Labs (experimental)" in the first release, with plain copy about the risks. **Don't** copy Inbox Zero's habit of selling Early Access features as headline features (PROD §9.3). | Trivial. | It matches the roadmap's "phase 5, optional" status (AUDIT §1) without deleting the work. |
| 10 | **An emulated test environment** (ARCH §9, the Playwright "emulated" mode against a fake mail server) | A fixture site of hostile and normal pages for agent browser tests and for the screenshot verification AGENTS.md already requires. | Low to medium. | It makes the eval work in #2 reproducible, and gives UI verification a stable target. |
| 11 | **Visible follow-through on the top complaint** (TRAC §5.2) | Treat Arc import as rac's equivalent of "local LLM support". Ship it and say so loudly. | See section 8. | It's the single feature that turns the Arc shutdown into rac installs. |
| 12 | **Audience capture that collects no data** (TRAC §4: Inbox Zero uses a newsletter) | A releases Atom feed, "Watch → Releases" on GitHub, and an RSS link on the site. No email collection. | Trivial. | rac currently has *no* way to tell interested people when it ships (AUDIT §6). |

---

## 7. What rac should not copy

1. **Mislabeling the license, or self-reported trust claims.** Inbox Zero calls itself "AGPL/open source" while adding restrictive terms (PROD §5.3). It says "SOC 2 Type 2 certified" with 0 public documents, and its own blog says that certification doesn't exist (PROD §6). rac's version of this risk is its *unbacked slogans*: "never slower than Helium" has no benchmark, and "a thin layer" sits on 217 touched files (AUDIT §2, §4). Don't add more of those. Back up or soften the existing ones.

2. **A telemetry and marketing stack.** PostHog `identify(userEmail)`, GTM, Sentry with possible prompt capture, Crisp, and conversion pixels (ARCH §8, §7 S7; PROD §6). Any of these breaks rac's first never-compromise rule. Inbox Zero's growth didn't depend on product analytics for the channels rac would use (PH, HN, SEO).

3. **Feature sprawl across surfaces.** Slack, Teams, and Telegram bots, a meeting recorder, a booking engine, SCIM, and a 628k-line single app (ARCH §12). For rac every feature is permanent rebase debt (AUDIT §2). Inbox Zero's founder advises "niche down instead of trying to out-feature" and then didn't follow his own advice (TRAC §6).

4. **Evals that don't gate, and security tests that test the wrong layer.** Inbox Zero's evals run only on `workflow_dispatch`, and its first injection case hides the payload in `display:none`, which the sanitizer removes before the model sees it (ARCH §5.5). Copy the suite, but make it block releases and target the model and policy layers.

5. **Classing destructive actions as low risk, or enforcing tool scope only through the prompt.** DELETE and MARK_SPAM are rated "low", and `manageInbox` executes with scope enforced only by prompt (ARCH §5.3). rac already always blocks closing the user's tabs and always shows a card for risky verbs (AUDIT §3). Keep it that way.

6. **A private build overlay.** If the hosted product differs from public code (ARCH §11), the core trust claim is undermined, as an HN commenter noted (TRAC §5.2). rac's release must be built entirely from the public repo in public CI.

7. **Fast self-merges without a gate.** Inbox Zero gets away with a 0.9 h median self-merge (TRAC §1.5) because CI catches regressions (ARCH §9). rac already merges in a median of 1.6 h on PRs up to +9k lines (AUDIT §5). It shouldn't keep doing that before #1 in section 6 exists.

8. **Default outbound actions the user didn't ask for.** Inbox Zero's Cold Email rule emails senders by default (PROD §7.2). rac's closest analog is the Option+hover link summary that requests a site the user never opened (AUDIT §3). Keep it opt-in and disclosed. Don't add more silent outbound behavior.

9. **Lifetime deals and affiliate-driven reviews.** Lifetime users are a cost center for AI, and paid "reviews" damage trust (TRAC §3.2, §4.4). rac has no revenue to share anyway, so it shouldn't start a reputation channel it can't keep honest.

---

## 8. The five changes rac should make in the next 30 days (by ~2026-11-24), ranked by impact

Context: Arc shuts down on 2026-12-22, about 58 days from 2026-10-25 (AUDIT §6). Thirty days leaves about four weeks of public availability before the shutdown, which is the minimum to catch the migration wave.

**1. Freeze features, sync to Helium 0.20.1.1 / Chromium 156, and ship a signed, notarized release from it, with the update path proven.**
- **Sync.** Freeze ai/agent feature work today. Run the untested `docs/operations/upstream-sync.md` procedure against helium-macos 0.20.1.1, which is seven releases and two Chromium majors ahead (ERRATA; AUDIT §5). Expect the work to concentrate in the 320 `ui/views` hunks and in the hot files (`ui/BUILD.gn`, `browser_view.cc`, `vertical_tab_strip_region_view.cc`, AUDIT §2). Write down what broke, so the procedure becomes real.
- **Release.**
  - Get `build.yml` green **on `main`**, not on a side branch (AUDIT §5). The signing and notarization secrets exist (ERRATA), so prove they're actually used and that the ad-hoc fallback in `sign_and_package_app.sh` (AUDIT §5) did not trigger. Check with `codesign -dv` and `spctl -a` on the artifact.
  - Before announcing, publish 0.1.0 and then 0.1.1 (versions only go up, AUDIT §7.1) to a test install. That proves the Sparkle feed, the signature, and that Keychain doesn't prompt across an update (the AUDIT §6 inference).
  - If the 10-phase CI can't finish reliably within the window, decide explicitly whether a signed build from the maintainer's own tree is acceptable for 0.1.x. [inference] It is acceptable only if the signing identity and feed are the permanent ones.
- **Why first:** with no release, nothing else matters. A release two majors behind would ship known Chromium security bugs (AUDIT §7.2), and every month of delay makes the first sync bigger.

**2. Build Arc import (spaces, pinned tabs, favorites, bookmarks, history) as the onboarding headline.**
- It's absent today (AUDIT §1, §7.7). [inference] Reuse Chromium's existing importer for bookmarks and history where it applies, and write a rac-owned importer that maps Arc's sidebar structure onto rac spaces, favorites, and pinned tabs.
- Put it in new files under the spaces/pinned code, wired in with a small hook in onboarding, so it adds few upstream hunks.
- Scope it narrowly: one-way, one shot, from a closed Arc profile. Test it on a copy of a real Arc profile, never the maintainer's live data (AGENTS.md "Ways to hurt yourself" #3, cited in AUDIT).
- **Why second:** it's the one feature that converts the shutdown into installs. rac's competitors are shipping (Ardia with 70 releases, Yab with 35+, AUDIT §6), and switching cost is the main barrier.

**3. Fix the agent's default before strangers can use it.**
- In the first release, put the agent behind "Labs", off by default even when AI chat is on.
- Change the default level from `auto` to `careful`. Alternatively, add two cards at `auto`: navigation to an origin the user didn't name, and typing after a cross-origin read in the same turn. Update the `AutoAsksOnlyForRiskAndForeignTyping` expectations to match (ERRATA).
- Add a minimum eval set of 10–20 hostile-page cases built around the four-step chain in AUDIT §3, run manually before each release.
- **Why third:** the audit calls this the project's "single biggest security exposure" (AUDIT §3). Exploiting it once against a real user's logged-in profile would destroy the privacy brand, which is the one place rac clearly beats Inbox Zero (section 4).

**4. Turn on a real gate: branch protection, PR-only `main`, and a required job that compiles and runs rac's five test targets.**
- Delete the pass-on-timeout behavior from `sanity.yml`, or rename it so nobody mistakes it for a build (AUDIT §5).
- Fix or remove Pullfrog.
- If per-PR runs are too slow, run the job nightly on `main` and make release tagging require a green nightly.
- Add a test that asserts no AI or agent services are constructed when AI is off. It's cheap, and it backs the "AI off costs nothing" claim (AUDIT §3).
- **Why fourth:** it's what Inbox Zero actually does that rac doesn't (section 3, items 2 and 3). It doesn't directly win users in 30 days, but it keeps the post-release fix cadence from breaking the browser.

**5. Make the public story true and reachable, then launch.**
- Detach or rename the GitHub repo so it stops reading as a Helium fork. Set the description to rac's own and point the homepage at racbrowser.com (AUDIT §0).
- Remove "a thin layer on top of Helium" (AUDIT §2).
- Either run one startup, tab-switch, and scroll comparison against Helium and publish the numbers, or soften "never slower than Helium" (AUDIT §4, §1 phase 4).
- Add SECURITY.md and a releases feed (section 6, #8 and #12).
- Publish an "Arc is shutting down: move to rac in 5 minutes" page and rac-vs-Arc, Dia, and Zen comparison pages. Flip `RELEASE_READY`, and launch on Show HN and Product Hunt the day the signed build and Arc import are both live.
- **Why fifth:** distribution without a release is pointless, so it depends on 1–2. Without it, though, the release reaches the same 2 unique visitors (AUDIT §0).

Explicitly *not* in the 30 days: the command bar, boosts, bangs design, media controls, more agent tools, and fixing ACP cold-start latency. Each is either new rebase debt or polish on a feature that should be in Labs.

---

## 9. Where I disagree with the dossiers

1. **AUDIT body: "No Apple Developer account … signs ad hoc … Gatekeeper wall … Keychain prompts after each update."** The ERRATA supersedes all of this. So risk #1 in AUDIT §7 is overstated: the problem is an *unproven* path, not a *missing* one. The Keychain inference (AUDIT §6) mostly falls away if Developer ID signing works. There's a leftover discrepancy the audit doesn't flag: the body cites the docs as saying `PROD_MACOS_*` secrets "are not configured" and "team ID empty" (AUDIT §1, §6). If the docs say that, the docs are now wrong, which is itself a finding.

2. **AUDIT §2: "a 110k-line patch stack, about two thirds the size of a mid-sized app."** This overstates. Patch lines include diff context and 26k lines of patch-on-patch rework. The audit's own better numbers are about 43k lines in new files and +3,429/−1,096 lines in 871 upstream hunks (AUDIT §2 table). For rebase burden, hunks and hot files are the measure that matters, and that measure is bad enough on its own. "Thin layer" is still false, but the honest rebuttal is "217 upstream files and 871 hunks", not "110k lines". Comparing raw size with Inbox Zero's 363k non-test lines (ARCH §0) would be meaningless either way.

3. **AUDIT §7.7: rac "spent its runway on the feature least likely to make an Arc refugee switch."** This is an inference stated as fact. Arc's own successor (Dia) is AI-first, so some Arc refugees want AI. The audit also lumps AI chat and the agent together (57%). The defensible criticism is about *ordering and risk*: the agent was built before the release, Arc import, and the sync, and it ships with a permissive default. It isn't that AI was the wrong bet.

4. **AUDIT §0 / §6: "zero measured demand (2 unique visitors in 14 days)."** rac has never been announced, and its download page is hidden (`RELEASE_READY = false`). Low traffic measures zero marketing, not zero demand. Any demand signal before launch is meaningless.

5. **AUDIT §7.5 ranks "AI-only review / 0 human approvals" as a separate top-5 risk.** TRAC §1.5 shows Inbox Zero's founder self-merges 94% of his PRs with a 0.9 h median, and the product still functions, because CI gates it (ARCH §9). The real defect is AUDIT risk #4, no CI. Missing human approvals matter mainly *because* there's no automated gate. They aren't an independent risk of the same weight. (Second-human review of the roughly 17k lines of security-critical agent code would still be valuable. It just isn't achievable for a solo project, so it shouldn't be ranked as if it were.)

6. **AUDIT §5 / §7.2: "A browser that ships two majors behind ships with known, public Chromium security bugs."** That's correct about the future, but rac currently ships nothing. More important is something the audit leaves out. [inference] rac's own work spans 23 days, yet it's two Chromium majors (about 8 weeks) behind, so the base was probably already stale when rac forked. Helium also shipped seven releases in that span (ERRATA). The real sync cadence may be *faster* than the "monthly" the audit assumes.

7. **ARCH §5.3: "I found no default system rule that sends [I] … the default posture is drafts, not sends."** This contradicts PROD §0.3 and §7.2, which document that the default Gmail Cold Email rule sends a "Notify sender" email automatically. That may be a separate action type from REPLY/SEND_EMAIL, but it is an automatic outbound email by default. The architecture dossier's safety summary is too generous here.

8. **ARCH §5.3: "Only the first [layer] is model-dependent; the other three are structural."** That's overstated by ARCH's own evidence. `manageInbox` scope is enforced "only by prompt", and custom MCP tools that a user enables run inside an email-driven agent (ARCH §5.3 Layer 3 and 4 notes). Two of the "structural" layers have model-dependent holes.

9. **ARCH §9 / §12: "very high test investment" (test/source ratio of about 0.92).** A ratio of lines says nothing about the quality of the tests on the paths that matter. The one security eval the dossier inspected was aimed at the wrong layer (ARCH §5.5), and evals don't gate. Quantity is real. Its value on safety-critical paths is unproven.

10. **TRAC §2.4: the estimate of about 400 paying seats.** It stacks a blended price assumption on a claimed, unverified ">$10K MRR" from Oct 2025, which is a year old. The same figure ($10K MRR) is also claimed for June 2024. [inference] That reading is consistent with flat revenue for 16 months, or with ">$10K" being a lazy floor. The dossier doesn't flag either possibility. Inbox Zero's business viability is less certain than its traction headline suggests, and its own price roughly doubling since 2023 (TRAC §3.2) could point either way.

11. **PROD §0.2: "Hosted product is paid-only for AI."** ARCH §5.1 shows BYO-key users bypass the trial spend limit, and PROD §4 marks whether BYO removes the paid requirement as UNKNOWN. The headline is probably right, but it's stated more firmly than the evidence allows.

12. **Something no dossier covers: rac's dependence on Helium's servers, given Helium's posture toward AI-built work.** AUDIT §4 and §7.6 note that rac uses imput's servers for extensions, filter lists, spell check, and bangs "with no agreement". Helium bans AI-written contributions (AUDIT §5). [inference] A fully AI-built fork drawing on those services at public scale could be cut off unilaterally, which would break rac's privacy story overnight. That deserves a contingency plan before launch, not just a line in the risk list.
