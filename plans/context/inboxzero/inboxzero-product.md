# Inbox Zero: product dossier

Researched 2026-10-25. Method: fetched getinboxzero.com pages (HTML and the `Accept: text/markdown` variant), docs.getinboxzero.com (Markdown pages via `llms.txt`), security.getinboxzero.com, the GitHub repo (README, LICENSE, SECURITY.md, source files, releases, via `gh api` and raw.githubusercontent.com), and one web search for third-party coverage. No sign-up, no forms, no logged-in product access. Nothing below was observed inside the running app.

## Legend

- **FACT**: verifiable from a primary source (their repo code, license, docs, or policy text). The text may still be an unverified statement about the world; "FACT that they say X" is marked where that matters.
- **CLAIM**: their marketing or an unverifiable assertion.
- **UNKNOWN**: not stated, or I could not verify it.

Source shorthand: `site` = https://www.getinboxzero.com, `docs` = https://docs.getinboxzero.com, `repo` = https://github.com/elie222/inbox-zero, `raw` = https://raw.githubusercontent.com/elie222/inbox-zero/main.

## 0. Top findings

1. **License is not plain AGPL.** The repo LICENSE is AGPL-3.0 plus "Additional Terms": a commercial-monetization ban, and organizations with 5 or more business users need a paid enterprise license. GitHub reports the license as "Other" (NOASSERTION). Marketing says "open source under the AGPL" and the self-hosting docs never mention the restriction. (FACT; sources in section 5.3.)
2. **Hosted product is paid-only for AI.** The email client is free; every AI feature needs Starter ($20/mo, $18 annual) or higher, with a 7-day trial that requires a credit card. (FACT; `site/pricing`, `site/enterprise` FAQ.)
3. **Default behavior is automatic organizing plus drafting, not auto-sending.** New rules label, archive, and pre-draft. Drafts are not auto-sent. But the default Cold Email rule on Gmail also emails the sender ("Notify sender"), which is an automatic outbound message. (FACT; docs.)
4. **Mail access is broad.** Gmail `gmail.modify` + `gmail.settings.basic`; Microsoft `Mail.ReadWrite`, `MailboxSettings.ReadWrite`, and `Mail.Send` (gated by a flag). Email content, subjects, and addresses are sent to third-party LLMs. (FACT; repo code and privacy policy.)
5. **Security claims are self-reported.** SOC 2 Type 2 and Google CASA Tier 2 appear only on their own pages. No auditor, report, period, or scope is public (the trust center shows "0 Documents"). Wording is inconsistent ("compliant" vs "certified" vs "fully certified"). (CLAIM.)
6. **Privacy policy contradicts itself on retention.** "We do NOT permanently store full email content" next to "We DO store ... summaries and analysis of your email history." "Zero Data Retention" heading next to "not stored beyond what is required for abuse and misuse monitoring" (that is not zero retention). Terms of Service last updated July 2023 and does not mention AI.
7. **Marketing and docs disagree in places.** Reply Zero is a headline feature but docs call it "Early Access." MCP "can never send email" (marketing) versus an optional `mcp:send` scope (docs). "iOS & Android" versus Android "older version, update coming." Changelog's newest entry is Aug 2024.
8. **Scale of the surface.** Rules engine, chat, bulk tools, analytics, calendar, meeting briefs, meeting notetaker, attachment filing, Slack/Teams/Telegram, MCP, CLI, public API, orgs, SSO/SCIM, email client (web, desktop, iOS), Gmail tab extension. Much of it is on paid tiers.

## 1. What it is and who it is for

| Item | Content | Status | Source |
|---|---|---|---|
| Their one-liner (site) | "Inbox Zero is an open-source AI email assistant for Gmail and Outlook." | CLAIM ("open-source" qualified by section 5.3) | https://www.getinboxzero.com/ (also `llms.txt`) |
| Their one-liner (repo description) | "The world's best AI personal assistant for email. Open source app to help you reach inbox zero fast." | CLAIM | `gh api repos/elie222/inbox-zero` |
| README title | "Inbox Zero - your 24/7 AI email assistant and email app" | CLAIM | `repo` README |
| README positioning | "Open source alternative to Fyxer, but more customizable and secure. We also offer an email app, an open source alternative to Superhuman." | CLAIM | `repo` README |
| README structure | Two parts: "an AI email assistant that works in the background on your Gmail or Outlook account, and an email client. Each works on its own." | FACT (as a description) | `repo` README |
| Mission | "To help you spend less time in your inbox, so you can focus on what matters most." | CLAIM | `repo` README |
| Homepage hero (browser HTML) | "Meet your AI email assistant that actually works" / "organizes your inbox and calendar, drafts replies in your voice, and helps you reach inbox zero fast. Never miss an important email again." | CLAIM | https://www.getinboxzero.com/ |
| Audience (about page) | "founders, operators, and professionals who get more email than they can reasonably handle by hand ... without locking you into a closed inbox replacement" | CLAIM | https://www.getinboxzero.com/about |
| Audience (plans) | Starter: "individuals, entrepreneurs, and executives". Plus: "power users who need integrations". Professional: "teams and growing businesses handling high email volumes". Enterprise: SSO/SCIM/on-prem. | CLAIM | https://www.getinboxzero.com/pricing |
| Vertical landing pages | Founders, small business, creators, realtors, customer support, e-commerce, MSPs, property management, law firms, accounting firms, insurance, recruiting, construction, travel advisors, executive assistants, ops managers | FACT (pages exist) | https://www.getinboxzero.com/sitemap.xml |

**Plain words.** A layer on top of your existing Gmail or Outlook mailbox. It reads incoming mail with LLMs, applies labels/categories, archives or moves some mail, and writes draft replies in your style. It adds cleanup tools (bulk unsubscribe/archive), analytics, calendar-aware features, chat control (in-app, Slack, Teams, Telegram, MCP clients), and a separate full email client. The company runs a hosted SaaS and also publishes the code.

Company: Inbox Zero Inc., 131 Continental Dr, Suite 305, Newark, Delaware 19713, USA (FACT, `site/privacy` s1.3). Founder named in the repo/blog: Elie Steinbock (handle elie222; CLAIM from their own blog, https://www.getinboxzero.com/blog/post/soc-2-compliant-email-tools).

## 2. Feature inventory

Plan column is from https://www.getinboxzero.com/pricing and the docs (links per row). "AI?" = whether an LLM is involved per the docs. Status: **Shipped** = documented as available with usage steps; **Early Access** = docs say "not yet available on all accounts"; no feature in the sources is labeled "coming soon" (UNKNOWN whether a public roadmap exists beyond the Featurebase roadmap link; I did not open it).

### 2.1 AI assistant (hosted, background)

| Feature | What it does | AI? | Plan | Status | Source |
|---|---|---|---|---|---|
| AI rules (Assistant) | Plain-English instructions become rules: a condition (AI instruction and/or static match on From/To/Subject) plus actions. One rule per email by default; multi-rule selection optional. "Apply to threads" toggle. Test tab, History, "Fix" workflow, learned patterns. | Yes (condition matching, rule generation) | Starter+ (AI requires paid plan) | Shipped | https://docs.getinboxzero.com/essentials/email-ai-personal-assistant.md |
| Rule actions | Label, move to folder, archive, delete, draft reply, send reply, forward, send email, mark read, star, mark spam, add to digest, call webhook, Todoist task, notify in Slack/Teams/Telegram, deliver draft to chat for review, notify sender | Partly (`{{ai text}}` placeholders generate content) | Starter+; digest needs Plus; Todoist is an Early Access integration | Shipped (Todoist: Early Access) | same page; https://docs.getinboxzero.com/essentials/context-integrations.md |
| Delayed actions | Supported actions run after 1 minute to 90 days | No | Not stated | Shipped | same rules page |
| Call webhook | Sends rule and email metadata to an external HTTP endpoint | No | Not stated | Shipped | https://docs.getinboxzero.com/essentials/call-webhook.md (listed in index; body not read) |
| Smart categories / sorting | Standard categories seeded in code: To Reply, Newsletter, Marketing, Calendar, Receipt, Notification, Cold Email (+ opt-in OTP). Also system rules Awaiting Reply, FYI, Actioned. Onboarding lets the user choose labels. Marketing and Cold Email default to label + archive on Gmail; Outlook uses move-to-folder. | Yes | Starter ("Sorts and labels every email") | Shipped | `raw/apps/web/utils/rule/consts.ts`; https://www.getinboxzero.com/pricing |
| Auto-drafts / reply drafting | Drafts replies for mail needing a response, into the Drafts folder, in the user's voice. Controls: auto-draft on/off, draft confidence (All / Standard / High), writing style, personal instructions, signature, draft knowledge base. Docs: "The assistant does not send these drafts automatically." | Yes | Starter; "Limited" knowledge base on Starter, "Unlimited" on Plus+ | Shipped | https://docs.getinboxzero.com/essentials/assistant-settings.md; pricing comparison table |
| Learning from edits | "Editing generated drafts also helps the assistant learn over time." Learned sender/domain patterns per rule. | Yes | Starter+ | Shipped (mechanism undocumented) | assistant-settings page |
| Calendar-aware drafting / AI scheduling | Checks connected calendars, restricts to weekly availability, drafts with a free time or a booking link | Yes | Not stated per feature | Shipped | https://docs.getinboxzero.com/essentials/calendar-integration.md |
| Booking links | Inbox Zero booking page, or share an existing Calendly/Google/Microsoft Bookings URL | No | Not stated | Shipped | https://docs.getinboxzero.com/essentials/booking-links.md (index only) |
| Cold Email Blocker | AI classifier driven by the "Cold Email" rule's prompt. Senders who emailed before always pass. Default actions on Gmail: label `Cold Email`, archive, notify sender. Outlook: move to `Cold Email` folder. Applies only to new mail, not backlog. Not-cold feedback list. Menu item appears for Google accounts; Outlook uses the rule. | Yes (LLM by default; optional "decision model") | Starter | Shipped | https://docs.getinboxzero.com/essentials/cold-email-blocker.md; https://docs.getinboxzero.com/hosting/llm-setup.md |
| Reply Zero / follow-ups | `To Reply` and `Awaiting Reply` labels; follow-up reminders (default 3 days, weekends excluded) with optional auto-drafted nudges; delivery to chat | Yes | Not stated on pricing grid | **Docs say Early Access** while site nav, README and a landing page market it as a core feature | https://docs.getinboxzero.com/essentials/reply-zero.md; https://docs.getinboxzero.com/ (Early Access list); https://www.getinboxzero.com/reply-zero-ai |
| Email digest | Scheduled summary of selected rules' mail | Yes | Plus+ ("Plus plan or higher") | Shipped | assistant-settings page; pricing |
| Meeting Briefs | Briefing before calendar events with external guests: attendee info, recent emails, past meetings (6 months), web research. Default 4 hours before (max 48). Email delivery default; Slack/Teams/Telegram optional. | Yes | Listed on Starter ("Pre-meeting briefings") | Shipped | https://docs.getinboxzero.com/essentials/meeting-briefs.md; pricing |
| Meeting Recorder / "AI meeting notetaker" | Visible bot joins Google Meet / Zoom / Teams calls, transcript, summary, action items, recap email, follow-up draft. Requires calendar connection. | Yes | **Plus+** (docs: "Plus plan or higher") | Docs list it under "Early Access: not yet available on all accounts" yet pricing lists it as a shipped Plus feature | https://docs.getinboxzero.com/essentials/meeting-recorder.md; pricing |
| Auto-file attachments | Analyzes attachments, files to Google Drive / OneDrive folders per a plain-English prompt; asks when unsure; learns from corrections | Yes | Plus+ | Shipped | https://docs.getinboxzero.com/essentials/auto-file-attachments.md |
| Context Integrations | Read-oriented lookups during drafting and briefs: Notion, Stripe, Linear, Attio, Intercom, Monday.com, Todoist (write-only), plus HubSpot, Salesforce, Airtable, Sheets, Slack, Asana, ClickUp, Jira, Zendesk, QuickBooks, Calendly via Composio, and Pipedream | Yes | Plus+ | **Early Access** | https://docs.getinboxzero.com/essentials/context-integrations.md |
| Sensitive-data protection | Policy Off / Redact / Block for detected credentials and card numbers before an AI request. Self-hosted default `ALLOW` (no scanning). Scanner is "not a full DLP or PHI classifier." | n/a | Not stated | Shipped; hosted default UNKNOWN | https://docs.getinboxzero.com/essentials/security-and-data.md; https://docs.getinboxzero.com/hosting/llm-setup.md |

### 2.2 Chat and agents

| Feature | What it does | AI? | Plan | Status | Source |
|---|---|---|---|---|---|
| In-app AI Chat | Search/summarize mail, read PDF/DOCX/TXT/CSV/HTML attachments, archive/delete/label/unsubscribe, draft email (confirmation card before send), manage rules and settings, check calendar, remember preferences, chat history, image upload | Yes | Not stated per feature (AI needs paid plan) | Shipped | https://docs.getinboxzero.com/essentials/ai-chat.md |
| Slack | OAuth app. DM or @mention the bot; rule notifications; draft review with send/edit/archive/mark-read cards; meeting briefs, follow-ups, digests, filing alerts, scheduled check-ins. Private channels only, no public channels. | Yes | **Plus+** (pricing: "Slack integration") | Shipped | https://docs.getinboxzero.com/essentials/slack-integration.md; https://docs.getinboxzero.com/essentials/channels.md |
| Microsoft Teams | Chat and notifications via `/connect` command to bot. Draft editing/sending in Teams "not available yet"; other quick actions view-only. | Yes | Not stated (pricing names only Slack) | Shipped with limits | channels page |
| Telegram | Chat, notifications; can send a prepared draft, no editing; archive/mark-read quick actions are Slack-only | Yes | Not stated | Shipped with limits | channels page |
| MCP server | Remote Streamable HTTP MCP at `https://www.getinboxzero.com/mcp`. OAuth (S256 PKCE, dynamic client registration). Tools: `list_email_accounts`, `search_inbox`, `read_thread`, `create_draft`, `list/get/create/update/delete_rule`, `get_stats_by_period`, `get_response_time_stats`. Scopes: `mcp:read`, `mcp:write`, `mcp:send` (per-app approval), `offline_access`. Off by default; user toggles in Settings. Works with ChatGPT (developer mode), Claude, Claude Code, Cursor. | The MCP client's model, not Inbox Zero's | Not stated | Shipped | https://docs.getinboxzero.com/essentials/mcp.md; https://docs.getinboxzero.com/api-reference/mcp.md |
| Public HTTP API + CLI + OpenClaw skill | API key (`API-Key` header) scoped to one account. OpenAPI covers stats by period, response-time stats, rules CRUD, sender unsubscribe. npm `@inbox-zero/api` (`inbox-zero-api`). | No | Not stated | Shipped | https://docs.getinboxzero.com/api-reference/introduction.md (via llms.txt); https://docs.getinboxzero.com/api-reference/cli.md; https://www.getinboxzero.com/openclaw |

### 2.3 Cleanup and analytics (mostly non-LLM or lightly LLM)

| Feature | What it does | AI? | Plan | Status | Source |
|---|---|---|---|---|---|
| Bulk Unsubscribe | Groups newsletter/marketing senders with volume and read rate. Actions: Unsubscribe (uses List-Unsubscribe when available, also archives existing mail), Block (auto-archive future), Approve, Label future, Auto-archive, Archive all, Delete all. "Select N suggested" picks rarely-read senders. | Mostly no (read-rate heuristics). Sender classification method UNKNOWN. | Starter ("Bulk unsubscribe and archive emails") | Shipped | https://docs.getinboxzero.com/essentials/bulk-email-unsubscriber.md |
| Bulk Archive | Categorizes senders (Newsletter, Marketing, Receipt, Notification, Other) then archive / mark read / delete by category. Categorization takes "a few minutes." | Yes (categorization) | Starter | Shipped | https://docs.getinboxzero.com/essentials/bulk-archiver.md |
| Deep Clean | AI-assisted cleanup of older Gmail threads with 50-message preview, protections (needs reply, starred, future events, receipts), undo; never deletes | Yes | "active premium plan" | **Early Access, Gmail only** | https://docs.getinboxzero.com/essentials/deep-clean.md |
| Analytics | Volume (received/sent/read/archived), top senders/recipients, median/average response time, assistant activity. "Load more" imports older history. | No | Starter; team-wide analytics = Professional | Shipped | https://docs.getinboxzero.com/essentials/email-analytics.md; pricing |
| Organizations / teams | Roles Owner/Admin/Member, invites (14 days), org-wide shared rules (copied to members), consented analytics (member must opt in) | Rules are AI | Professional for "team-wide analytics"; invite flow also in onboarding | Shipped | https://docs.getinboxzero.com/essentials/organizations.md |
| Enterprise SSO / SCIM | SAML SSO and SCIM provisioning. Hosted: contact sales. | No | Enterprise (custom) | Shipped | https://docs.getinboxzero.com/hosting/sso.md; pricing |

### 2.4 Clients and platforms

| Surface | Details | Status | Source |
|---|---|---|---|
| Email client (web) | Split inbox, J/K/E/H/R/Z shortcuts, Cmd+K, all accounts in one inbox, team comments with @mentions ("never sent as email"), schedule send/snooze. Marketed as free. "Like Superhuman, but free"; "Half the price of Superhuman." | Shipped (marked "New") | https://www.getinboxzero.com/email-client; https://www.getinboxzero.com/ |
| Desktop | Electron app, Mac (Apple Silicon, Intel), Windows, Windows ARM. Version 0.1.21 on download page; GitHub releases `desktop-v0.1.21` (2026-10-21), v0.1.20 (2026-10-19), v0.1.19 (2026-10-10). Version 0.1.x suggests early maturity. | Shipped | https://www.getinboxzero.com/download; `gh api repos/elie222/inbox-zero/releases` |
| iPhone | Native Swift app; "not open source yet" (plan to open it). Can point at a self-hosted server URL. | Shipped | `repo` README; https://www.getinboxzero.com/mobile-app |
| Android | README: "an older React Native Android app." Download page: "Older version. An update is coming." Docs (mobile-apps) and homepage list "iOS & Android" without that caveat. | Shipped but stale (their words) | `repo` README; https://www.getinboxzero.com/download; https://docs.getinboxzero.com/essentials/mobile-apps.md |
| Browser extension "Inbox Zero Tabs" | Free; custom Gmail tabs from Gmail search queries; Chrome/Chromium and Firefox; Gmail only (not Outlook). Claims "100% private - all data stays in your browser with no tracking or data collection." Can sync label-based rules to tabs. | Shipped | https://docs.getinboxzero.com/essentials/inbox-zero-tabs-extension.md |
| Free web tools | Email deliverability checker, subject line analyzer, signature generator, Gmail quiz, cost calculators | Shipped | https://www.getinboxzero.com/tools |

### 2.5 Not found (UNKNOWN)

- Outlook parity: Cold Email Blocker UI and Tabs extension are Gmail-oriented; Deep Clean is Gmail-only (docs). Complete Outlook-versus-Gmail feature matrix not published.
- Per-feature plan mapping for Teams, Telegram, Chat, Bulk Archive, Reply Zero, Calendar is not given on the pricing page.
- Limits (emails per month, AI action caps, fair-use thresholds): none stated anywhere I could find.

## 3. Platforms, integrations, and access

| Item | Detail | Status | Source |
|---|---|---|---|
| Gmail / Google Workspace | Supported | FACT | https://docs.getinboxzero.com/introduction.md |
| Outlook.com / Microsoft 365 / Exchange | "fully supports" work/school and personal accounts. Managed tenants may need admin approval. Shared mailboxes accessed via your account are not supported. | FACT (docs) | https://docs.getinboxzero.com/essentials/outlook-guide.md |
| Other providers (iCloud, Yahoo, IMAP) | None mentioned | UNKNOWN (treat as unsupported) | all sources |
| Gmail scopes (code, hosted default) | Required: `userinfo.profile`, `userinfo.email`, `gmail.modify`, `gmail.settings.basic`. Optional (flag-gated): `contacts`, `contacts.other.readonly`. | FACT (source code) | `raw/apps/web/utils/gmail/scopes.ts`; self-host doc lists same |
| Google Calendar scopes | `calendar.readonly`, `calendar.events`, `calendar.freebusy` | FACT | `raw/.../gmail/scopes.ts`; docs/hosting/google-oauth |
| Google Drive scopes | `drive.file` (Standard) or `drive` (Full access, to use existing folders) | FACT | https://docs.getinboxzero.com/hosting/google-oauth.md |
| Microsoft Graph scopes | `openid, profile, email, User.Read, offline_access, Mail.ReadWrite, MailboxSettings.ReadWrite`, plus `Mail.Send` only if `NEXT_PUBLIC_EMAIL_SEND_ENABLED`; calendar: `Calendars.Read, Calendars.ReadWrite`; self-host doc also lists `Files.ReadWrite`; optional `Contacts.Read`, `People.Read` | FACT (code + docs) | `raw/apps/web/utils/outlook/scopes.ts`; https://docs.getinboxzero.com/hosting/microsoft-oauth.md |
| Can it send mail? | Getting-started says approve permissions "so Inbox Zero can read and organize messages, create drafts, and send messages." Privacy policy: "Send emails on your behalf as directed." Rule actions include Send reply / Send email / Forward. Note (my reading of Google's public scope docs, not their statement): `gmail.modify` permits sending. Hosted Mail.Send flag value UNKNOWN. | FACT (stated capability) | https://docs.getinboxzero.com/essentials/getting-started.md; https://www.getinboxzero.com/privacy |
| Actual hosted consent screen | Not observed (no sign-in) | UNKNOWN | n/a |
| Sync mechanism | Gmail push via Google Pub/Sub; Outlook via Graph webhooks (self-host docs). Hosted retention of tokens: "Authentication Data ... OAuth tokens" stored (privacy s2). | FACT | https://docs.getinboxzero.com/hosting/google-pubsub.md; https://docs.getinboxzero.com/hosting/security-hardening.md |
| Calendars | Google Calendar, Outlook Calendar | FACT | calendar-integration page |
| Drives | Google Drive, OneDrive (SharePoint mentioned in the Outlook table) | FACT | auto-file page; outlook-guide |
| Chat | Slack, Microsoft Teams, Telegram | FACT | channels page |
| Context tools | Notion, Stripe, Linear, Attio, Intercom, Monday.com, Todoist, Composio-hosted (HubSpot, Salesforce, Airtable, Sheets, Slack, Asana, ClickUp, Jira, Zendesk, QuickBooks, Calendly), Pipedream | FACT, Early Access | context-integrations page |
| Meeting platforms (notetaker) | Google Meet, Zoom, Microsoft Teams. Webhook path `/api/recall/webhook` suggests Recall.ai as the bot vendor (my inference from docs path; not on subprocessors list). | FACT / inference flagged | meeting-recorder page; security-hardening page; subprocessors page |
| Slack/Teams/Telegram on hosted | Subprocessors page lists them as "Customer-authorized services" | FACT | https://www.getinboxzero.com/subprocessors |

## 4. AI: providers, keys, local models, data, retention

| Item | Detail | Status | Source |
|---|---|---|---|
| Hosted providers | Subprocessor list (updated Sep 22, 2026): OpenRouter (AI infrastructure), OpenAI, Anthropic, Google Vertex AI / Gemini, Amazon Web Services / Bedrock, Groq, "TypeSafe AI". "AI model providers listed below may be used directly or through OpenRouter, depending on the model and provider configuration." Specific model per feature on hosted: not published. | FACT (list) / UNKNOWN (models) | https://www.getinboxzero.com/subprocessors |
| BYO key (hosted) | Yes, optional: Settings > email account > AI Model. Providers in UI: Anthropic, OpenAI, Azure OpenAI, Google, Groq, Cerebras, OpenRouter, Vercel AI Gateway. "Inbox Zero covers AI costs by default." Whether a BYO key removes the paid-plan requirement: UNKNOWN. | FACT | https://docs.getinboxzero.com/essentials/api-keys.md |
| Self-host providers | OpenAI, Anthropic, Azure OpenAI, Azure AI Foundry, Google Gemini, Vertex, OpenRouter, Groq, Cerebras, Vercel AI Gateway, AWS Bedrock, **Ollama**, any OpenAI-compatible endpoint (LM Studio, vLLM, LiteLLM), plus experimental `codex-cli` and `claude-code`. Tiered model config: DEFAULT, ECONOMY, CHAT, DRAFT, NANO, with ordered fallbacks. | FACT | https://docs.getinboxzero.com/hosting/llm-setup.md; https://docs.getinboxzero.com/hosting/environment-variables.md |
| Local models | Possible only via self-hosting (Ollama / OpenAI-compatible). Not offered on hosted. Quality of small local models for these prompts: UNKNOWN. | FACT (capability) | llm-setup page |
| Data sent to models | Privacy policy: "Email subject lines, email body text, sender and recipient information, timestamps, and folder/label information." Docs add: attachments (chat and auto-file read PDF/DOCX/etc.), calendar context, meeting transcripts, web research, tool results from integrations. | FACT | https://www.getinboxzero.com/privacy s5.1; docs pages above |
| Training | "We do not allow those providers to train their AI models using your data." Site marketing: "no AI training, no funny business." | CLAIM (contractual terms not published; no DPA shown) | https://www.getinboxzero.com/privacy s5.1; https://www.getinboxzero.com/ |
| Retention at providers | Policy heading "Zero Data Retention", body: providers "do not store your data on their servers beyond what is required for abuse and misuse monitoring." That is not zero retention. | CLAIM, internally inconsistent | https://www.getinboxzero.com/privacy s5.2 |
| Redaction before send | Optional sensitive-data policy (credentials, card numbers). Off by default for self-host (`ALLOW`); hosted default UNKNOWN. | FACT (feature) | llm-setup; assistant-settings |
| Model quality caveats | Docs: "AI output can be incomplete or incorrect," rules may mis-match, drafts may assume things. | FACT (their disclaimer) | https://docs.getinboxzero.com/essentials/security-and-data.md |
| Stored derived data | Privacy: "Summaries and analysis of your email history," sender addresses, metadata. Meeting transcripts and summaries stored until "Delete notes." | FACT (stated) | privacy s2; meeting-recorder page |

## 5. Pricing, plans, self-hosting terms

### 5.1 Hosted plans (USD, per user per month)

| Plan | Monthly billing | Annual billing | Annual total | Discount shown | Includes (in their words) |
|---|---|---|---|---|---|
| Free ("Email app") | $0 | $0 | $0 | n/a | "A fast email app for Gmail and Outlook. Free on web, desktop, and iPhone." No AI. |
| Starter | $20 | $18 | $216/yr | "Save 10%" | Sorts and labels every email; drafts replies in your voice; blocks cold emails; bulk unsubscribe and archive; email analytics; pre-meeting briefings. Knowledge base: "Limited." |
| Plus (marked "Popular") | $35 | $28 | $336/yr | "Save 20%" | Everything in Starter plus: 2 email accounts included per user; AI meeting notetaker; Slack integration; app integrations (Notion, Stripe, and more); email digests; auto-file attachments; unlimited knowledge base. |
| Professional | $50 | $42 | $504/yr | "Save 16%" | Everything in Plus plus: team-wide analytics; priority support; dedicated onboarding manager. |
| Enterprise | Custom | Custom | Custom | n/a | SSO, SCIM, on-premise deployment, dedicated account manager (contact sales). |

Source: https://www.getinboxzero.com/pricing, markdown variant of https://www.getinboxzero.com/ (exact annual totals). Arithmetic checks out (18x12=216, 28x12=336, 42x12=504). FACT as published prices.

Other pricing facts (FACT, from pricing FAQ / enterprise FAQ):
- Trial: 7 days on AI plans; "A credit card is required to start your trial, but you won't be charged until the trial ends." (https://www.getinboxzero.com/enterprise)
- Plan changes take effect immediately, prorated. Payments via Stripe, "all major credit cards." (The subprocessors page also lists Lemon Squeezy for billing; relation to Stripe not explained.)
- Refund: email within 14 days of upgrading.
- Discounts for students, nonprofits, open-source projects by email request.
- Cancel anytime; active until period end.

**Gaps and oddities:**
- Whether Starter includes 1 email account is implied only by Plus's "2 email accounts included per user"; Starter and Professional account caps are not stated. Professional includes Plus so presumably 2, but unconfirmed. UNKNOWN.
- "Per user" billing combined with "Organizations" and "premium seats" (docs) means team cost = seats x price; seat mechanics are only partly documented.
- No usage caps stated. UNKNOWN whether "unlimited" applies.
- Docs say "Digests require Plus" and "Meeting recording requires Plus" and "Context Integrations require Plus"; pricing shows digest and notetaker in Plus (consistent). Pre-meeting briefs in Starter but integrations that enrich briefs need Plus.
- The Starter label on the site says $20 at monthly toggle in the comparison table even when the card shows $18 (annual); not a contradiction, just the grid always uses monthly prices.
- Hosted homepage claim "AI drafts and a sorted inbox from $18/month, half what Superhuman charges" uses the annual price.

### 5.2 Self-hosting (FACT unless noted)

- Entry: `npx @inbox-zero/cli setup` and `start`; Docker + Node 24+. Homebrew install also available. (https://docs.getinboxzero.com/hosting/quick-start.md)
- You supply: Google OAuth project (consent screen, scopes, Pub/Sub for Gmail push) and/or Azure app registration, an LLM provider/key (or Ollama), Postgres and Redis (Upstash HTTP interface or equivalents), optional Resend/Tinybird/Sentry/Axiom. Unverified Google apps show a "This app isn't verified" screen and need test users (docs, google-oauth page).
- Premium checks: `NEXT_PUBLIC_BYPASS_PREMIUM_CHECKS=true` is the documented default for self-hosting ("recommended"). So the self-hosted app has no paywall in the code.
- Deploy targets documented: Docker/VPS, Vercel, Kubernetes (Helm), AWS (EC2, Terraform, Copilot), GCP + Cloudflare Tunnel.
- Local dev: `pnpm local:start` with provider emulators and canned AI (README).
- Optional image proxy to hide user IPs from remote email images. (https://docs.getinboxzero.com/hosting/image-proxy.md)

### 5.3 License (important for any comparison)

- `repo/LICENSE` = GNU AGPL v3 **plus "ADDITIONAL TERMS FOR INBOX ZERO"** (FACT; I read the file):
  - "COMMERCIAL MONETIZATION RESTRICTION": no using it "for commercial purposes that involve monetizing the software itself, including ... selling access ... offering it as a paid service ... without explicit written permission from Inbox Zero Inc."
  - "ENTERPRISE USE LIMITATION": "If you are an organization with five (5) or more employees, contractors, or users who will use this Program for business purposes, you must obtain an enterprise license from Inbox Zero Inc. before using this Program."
  - Exemptions: personal, educational, research use, and organizations with fewer than five business users.
  - Copyright (C) 2025 Inbox Zero Inc.
- GitHub's license API reports key `other`, SPDX `NOASSERTION` (FACT; `gh api repos/elie222/inbox-zero`).
- Contradictory messaging (FACT that the texts differ): the email-client page says "The web and desktop email client is open source under the AGPL license" and shows an "AGPL-3.0" badge (https://www.getinboxzero.com/email-client). Self-hosting docs I grepped (quick-start, self-hosting, environment-variables, setup-guides) contain no mention of the 5-user enterprise-license rule. Enterprise page says "Open source and self-hostable for maximum enterprise control" while the license requires an enterprise license for 5+ business users.
- Consequence: by the OSI definition this is source-available / open-core-style, not open source (my assessment; the OSI definition prohibits field-of-use restrictions). The AI assistant, web app, and desktop client code are published in the repo; the iPhone app is not (FACT, enterprise FAQ).
- A competitor's blog independently flags the same catch (https://www.thisandthat.chat/blog/inbox-zero-review-2026). Treat as biased context, but the underlying LICENSE text is primary.
- There is also a `CLA.md` in the repo root (FACT that the file exists; contents not read).

## 6. Privacy and security claims

| Claim | Where | Type | Verifiability / notes |
|---|---|---|---|
| "SOC 2 Type 2 certified" (homepage, email-client page); "SOC2 Compliant" (footer, about); "We're fully certified for top-tier security" | https://www.getinboxzero.com/ ; https://www.getinboxzero.com/about | CLAIM | Trust center (https://security.getinboxzero.com) shows "SOC 2 Type 2 Compliant," "Powered by Comp AI" (a compliance-automation vendor), 23 policies, 37 controls, 14 subprocessors, **0 documents**. No auditor, audit period, scope, or report is public. Their own blog notes "there's no such thing as 'SOC 2 certified'" yet uses "certified" on the site. Report available under NDA/request: UNKNOWN. |
| "Google-verified by designated third-party security auditor, CASA Tier 2 accredited" | https://www.getinboxzero.com/enterprise ; blog "CASA Tier 2 approved by Google" | CLAIM | No assessor named, no date, no Letter of Validation shown. Web search found only Inbox Zero's own pages as sources. CASA must be renewed annually (general Google policy; date of their last assessment UNKNOWN). Google OAuth verification of the hosted app itself is plausible (the app serves public users) but I did not observe the consent screen. |
| GDPR role split | Privacy s1.2: controller for account data, processor for email content | FACT (stated) | No DPA link, no named DPO. Contact is the founder's address `elie@getinboxzero.com`. |
| What is stored | "We do NOT permanently store: full email content (body text); email subject lines (except as needed for active features)." "We DO store: sender information; summaries and analysis of your email history; email metadata needed for automation rules; temporary email summaries (deleted after feature completes)." "Email content is analyzed ... but is not retained in our systems beyond what is necessary." | CLAIM | Vague ("as needed", "necessary"). "Summaries and analysis of your email history" is a derived-content store with no stated retention period. Drafts, knowledge base, chat history, rule history, and meeting transcripts are also stored per docs but not itemized in the policy. |
| Retention period | Privacy s9: "only retain ... for as long as necessary." No numbers. | FACT (it says nothing concrete) | UNKNOWN actual periods. Account deletion available in Settings; revoking provider access is separate (FAQ). |
| Encryption | Privacy s8: "appropriate technical and organizational security measures." Trust center lists an "Encryption and Key Handling Policy." No statement of at-rest/in-transit algorithms or customer-managed keys. | Mostly UNKNOWN | Policy documents are not publicly readable (0 documents). |
| Google API Services User Data Policy / Limited Use | Privacy: adheres; no advertising use, no sharing "except as described" | CLAIM | The Limited Use statement is a legal commitment; verifiable only via Google's review. |
| "We do not ... Store your email content on our servers" | Privacy, Google and Microsoft sections | CLAIM | In tension with: meeting transcripts and summaries, draft knowledge base, chat attachments, the Tinybird analytics store, and "summaries and analysis." |
| Subprocessors | Page updated Sep 22, 2026 lists 20: Vercel, Neon, Upstash, Cloudflare, OpenRouter, OpenAI, Anthropic, Google Vertex/Gemini, AWS/Bedrock, Groq, TypeSafe AI, Tinybird, Axiom, Sentry, PostHog, Resend, Loops, Crisp, Stripe, Lemon Squeezy. Plus "customer-authorized": Google, Microsoft, Slack, Teams, Telegram. | FACT (published list) | Trust center shows 14 subprocessors including GitHub and Google Workspace (not on the public page): two lists disagree. |
| International transfers | SCCs or EU-US DPF providers | CLAIM | Hosting region(s) not stated. UNKNOWN whether EU data residency is offered for hosted. |
| Site telemetry | Homepage HTML loads Google Tag Manager (`GTM-NBXBG84N`) and a PostHog provider/pageview component (FACT, observed in served HTML). Privacy mentions PostHog and cookies generically. | FACT | Cookie banner/consent: a `NEXT_PUBLIC_COOKIE_CONSENT_ENABLED` env var exists (default `false`; doc says it shows a banner to EU/EEA/UK/CH visitors and holds back ad tracking until accepted). Whether hosted enables it: UNKNOWN. Privacy policy has no dedicated cookie section or cookie table (text I read). |
| App telemetry | Subprocessors: PostHog (product analytics and feature management), Tinybird (analytics), Axiom (logs), Sentry (errors), Crisp (support), Loops (customer comms). Repo `.env.example` includes Tinybird, Sentry, Axiom keys (all blank by default). | FACT for list; self-host default behavior UNKNOWN beyond blanks | Self-host telemetry-to-vendor behavior not audited. |
| Extension privacy | "100% private ... no tracking or data collection ... email data never leaves your device" | CLAIM | Plausible (client-side only) but extension source/permissions not reviewed. Unclear whether it ships in the monorepo. |
| Org analytics | Member analytics private by default; admin sees only if member opts in; admins cannot read email content via org page | FACT (docs) | Self-host env `AUTO_ENABLE_ORG_ANALYTICS` can flip default. |
| Vulnerability disclosure | `SECURITY.md`: GitHub advisories or `security@getinboxzero.com`; ack within 3 business days, assessment within 7 | FACT | https://github.com/elie222/inbox-zero/blob/main/SECURITY.md (read via API) |
| Public page `/security` | 404 | FACT | Security story lives at security.getinboxzero.com only |
| Terms of Service | Dated July 16, 2023; names "getinboxzero.com" as the party (not Inbox Zero Inc.); NY governing law; no AI, data-processing, SLA, or acceptable-use specifics | FACT | Stale compared with the May 4, 2026 privacy policy (Delaware entity). |
| Safety mechanisms (product) | Confirmation card before send in chat; rules can be tested; History + Fix; disable all rules per mailbox; Deep Clean never deletes and has undo; MCP draft-only by default | FACT (docs) | Good practice, but rules execute automatically once enabled ("Rules run automatically after they are enabled"). |

Mixed-verifiability summary: **Verifiable from primary source**: scopes (code), license, subprocessors list, docs behavior, OAuth/MCP spec details, pricing. **Marketing only**: SOC 2 outcome, CASA, "no training," "zero data retention," "never store email content," "100% private" extension.

## 7. Onboarding flow and defaults

### 7.1 Flow (docs + source)

Docs (https://docs.getinboxzero.com/essentials/getting-started.md): 1) Sign in and connect Gmail or Outlook (approve permissions to read, organize, create drafts, send). 2) Assistant guided setup with "a smart set of default rules." 3) Bulk Unsubscribe / Bulk Archive for backlog. 4) Optional: calendars, Channels (Slack/Teams/Telegram), Tabs extension, organization. 5) Personalize drafts in Assistant > Settings.

Source (`raw/apps/web/app/(app)/[emailAccountId]/onboarding/onboardingFlow.ts`, FACT as of main branch on 2026-10-25): hosted steps are a survey (role, company size, how you heard; skipped for self-host), then an intent question (AI assistant vs mail app), then for the AI branch: emails sorted, chat, draft replies, bulk unsubscribe, labels ("How do you want your inbox organized?"), draft ("Should we draft replies for you?" Yes, please / No, thanks), custom rules, invite team (if eligible), inbox processed. The mail-app branch has a single "mail app" step. The onboarding collects a "how you heard" survey (a data-collection point to note).

Marketing's version: "STEP 1 Connect your Google or Microsoft email ... STEP 2 ... Smart categories set up automatically ... STEP 3 Pre-drafted replies" (https://www.getinboxzero.com/ai-automation). Time claim: "Set up Inbox Zero in five minutes" (https://www.getinboxzero.com/case-studies), "Get started in minutes."

### 7.2 Defaults: does AI act automatically, or draft?

| Behavior | Default | Source |
|---|---|---|
| New incoming mail is classified and labeled | Yes, automatically, once rules are enabled | docs intro; "Rules run automatically after they are enabled" (security-and-data page) |
| "To Reply" mail | Labeled; a draft is created in Drafts (if the user chose drafts in onboarding; the question is explicit, default answer UNKNOWN) | docs intro; `consts.ts` (`draftReply: true`); StepDraft.tsx |
| Marketing | Label + **archive** on Gmail; move-to-folder on Outlook | `consts.ts` (`categoryAction: "label_archive"`) |
| Cold email | Label + archive + **email the sender (Notify sender)** on Gmail; move to folder on Outlook | https://docs.getinboxzero.com/essentials/cold-email-blocker.md |
| Newsletter, Calendar, Receipt, Notification | Label (Outlook: move to folder) | `consts.ts` |
| Auto-send replies | Not a default. "Auto draft replies ... does not send these drafts automatically." Send/forward actions are opt-in rule actions. | assistant-settings page |
| Deletion | Not default. Bulk delete asks for confirmation; Deep Clean never deletes | bulk-archiver, deep-clean pages |
| Backlog | Not touched by rules by default. Cold email applies only to new mail; Bulk tools are manual. | docs |
| MCP | Off until user enables | mcp page |
| Docs advice | "Begin with labeling, archiving, or marking messages as read. Add outbound actions ... after you are comfortable." | getting-started page |
| Learned patterns | Auto-created from user behavior and corrections; user can remove them | email-ai-personal-assistant page |

Critical notes: (a) mail is moved out of the inbox (archive) by default for marketing and cold email without a per-message review step, so a classifier error hides mail; the mitigation is labels, History, Fix, and "Not cold email." (b) The "Notify sender" default means the product sends mail on the user's behalf by default, which the "draft, not send" framing does not capture. (c) Default answer to the draft question in onboarding: UNKNOWN (UI choice shown; stored default not verified).

## 8. Positioning and messaging

| Item | Content | Type | Source |
|---|---|---|---|
| Category framing | "AI email assistant" + "email app" (two products, each standalone). "Like Superhuman, but free." "Half the price of Superhuman." "Open source alternative to Fyxer." | CLAIM | homepage; README |
| Headline | "Meet your AI email assistant that actually works" | CLAIM | https://www.getinboxzero.com/ |
| Subpitch | "A personal assistant at a fraction of the cost. Drafts replies, organizes, and labels emails ... works 24/7." "Get back an hour a day." | CLAIM | /ai-automation |
| Enterprise pitch | "Give every employee an AI executive assistant"; "Handoff everything but your genius"; "complete data sovereignty" via self-host | CLAIM | /enterprise |
| Differentiators claimed | Open source (inspect, self-host); works inside Gmail/Outlook ("without locking you into a closed inbox replacement"); SOC 2; no AI training; customizable plain-English rules; chat from Slack/Telegram/Teams; MCP | CLAIM | homepage, /about, /best-fyxer-alternative, README |
| Social proof: users | "Join 25,000+ professionals, including people at:" (logos not enumerated in text I fetched) and "Join 25,000+ others who spend less time on emails" | CLAIM; no definition of "professionals," no date, not on the plain-text/markdown homepage variant | e.g. https://www.getinboxzero.com/email-client, /enterprise, /reply-zero-ai |
| Social proof: emails processed | None stated | UNKNOWN | whole site |
| Social proof: GitHub | 12,805 stars, 1,632 forks, repo created 2023-07-12, last push 2026-10-23, 96 open issues, 47 open PRs, ~82 contributors listed | FACT (live API 2026-10-25) | https://github.com/elie222/inbox-zero |
| Testimonials | Joel Neuenhaus (Outbound Legal): "first tool ... that actually captured my voice"; Valentine Nwachukwu (Zaden Technologies): replaced his EA; Steven Tey (Dub): "Love this new open-source app"; Yoni Belson (LeadTrap); Slim Labassi (Boomgen); Alex Bass (Efficient App); Will Brierly (DreamKey); Jonni Lundy (Resend) | CLAIM (named, but unverified, some are tweets; several appear to date from early launch) | /reply-zero-ai, /block-cold-emails |
| Case studies | Clicks Talent ("processes thousands of emails a month"), DateNight, Cloud 9 Computing Group, JOCO | CLAIM | https://www.getinboxzero.com/case-studies |
| Comparison pages | vs Fyxer, Superhuman, Shortwave, Perplexity email assistant, Serif; "Best AI Email Assistants" directory | CLAIM (self-authored; e.g. "Both are SOC 2 compliant") | /best-fyxer-alternative etc. |
| Content footprint | 180+ blog URLs in the sitemap; programmatic SEO (industry pages, free tools) | FACT | https://www.getinboxzero.com/sitemap.xml |
| Changelog | Hosted on Featurebase (`/changelog` redirects to inboxzero.featurebase.app). Newest entry visible: Aug 28, 2024. Effectively stale as a release record, while the GitHub repo and docs are current. | FACT | https://go.getinboxzero.com/changelog |
| Status page | https://inbox-zero.openstatus.dev/ linked from footer | FACT (link exists; not inspected) | pricing HTML |

## 9. Inconsistencies, gaps, and critical notes

1. **Open-source label vs license.** See 5.3. Biggest comparison hazard: "open source" is true for code visibility and AGPL base terms, but the added restrictions (5+ business users need a license; no resale) mean the self-hosted route is not free for most organizations. Docs and marketing do not warn about it.
2. **"Free" scope.** "Free" applies to the email client only. All AI sits behind a paid plan with a card-required trial. A BYO-key route exists in settings but its effect on plan gating is undocumented.
3. **Feature maturity labels disagree.** Reply Zero, Meeting Recorder, Context Integrations, Deep Clean are in docs' "Early Access" section; Reply Zero and the notetaker are sold as headline/Plus features. "Coming soon" is not used anywhere I found; "Early Access" is the hedge.
4. **MCP send.** Landing page: "it can never send email on its own"/"no send tool." Docs: "cannot send email," but also an `mcp:send` scope "granted only when a client requests it" and `llms.txt` says "sending requires separate per-app approval." Tool list in docs shows only `create_draft`. Treat "never sends" as true by default, possibly false with `mcp:send`; verify against code before relying on it.
5. **Mobile.** Homepage "iOS & Android"; docs say apps exist for both; download page and README say Android is an old build awaiting update.
6. **Retention wording.** See section 6. The policy states both "not stored" and "stored summaries and analysis." There is no retention schedule.
7. **Compliance wording.** "Certified," "compliant," "fully certified," "CASA Tier 2 accredited/approved." Trust-center counts have changed between snapshots (search result showed 20 policies / 17 controls; page now shows 23 / 37), which suggests an actively edited, vendor-generated dashboard rather than a point-in-time attestation. The public subprocessor lists differ (14 vs 20).
8. **Stale legal text.** ToS from 2023, no mention of AI, sub-accounts, or meeting recording (which has recording-consent implications; the docs only warn the user to follow local laws).
9. **Meeting recorder consent.** Bot is visible ("Alex's Inbox Zero Notetaker"). Legal responsibility is pushed to the user (docs warning).
10. **Outbound email by default.** Cold-email "Notify sender" confirms live addresses to cold senders and sends mail from the user's account. Removable.
11. **Self-host friction.** Needs your own Google Cloud project; Google's sensitive-scope verification (and likely CASA) is not provided to self-hosters, who will see an "unverified app" warning (docs). So the "SOC 2 / CASA" claims apply only to the hosted service.
12. **Pricing grid clarity.** The compare-plans table text lost its check marks in my fetch; plan membership above was reconstructed from the card bullets and docs "Plus or higher" notes. Any row not backed by a card bullet is UNKNOWN.
13. **Not verified by me:** actual in-app UI, hosted default model(s), default state of the onboarding draft question, whether the hosted app shows a cookie banner, whether the trust-center SOC 2 report exists, any rate limits.

## 10. Source index

- https://www.getinboxzero.com/ (HTML and markdown variants), /pricing, /enterprise, /about, /email-client, /mobile-app, /download, /reply-zero-ai, /case-studies, /ai-automation, /block-cold-emails, /gmail-mcp, /cli, /openclaw, /privacy (Last Updated May 4, 2026), /terms (July 16, 2023), /subprocessors (Sep 22, 2026), /llms.txt, /sitemap.xml
- https://security.getinboxzero.com (Trust Center)
- https://go.getinboxzero.com/changelog -> https://inboxzero.featurebase.app/changelog
- https://docs.getinboxzero.com/llms.txt and the `.md` pages cited inline (introduction, getting-started, email-ai-personal-assistant, assistant-settings, cold-email-blocker, reply-zero, bulk-email-unsubscriber, bulk-archiver, email-analytics, ai-chat, calendar-integration, meeting-briefs, meeting-recorder, deep-clean, context-integrations, channels, slack-integration, auto-file-attachments, organizations, mcp, api-reference/mcp, api-reference/cli, mobile-apps, inbox-zero-tabs-extension, api-keys, security-and-data, outlook-guide, faq; hosting: quick-start, llm-setup, environment-variables, google-oauth, microsoft-oauth, sso, security-hardening, image-proxy)
- https://github.com/elie222/inbox-zero (README, LICENSE, SECURITY.md, releases, repo metadata) and raw source files: `apps/web/utils/gmail/scopes.ts`, `apps/web/utils/outlook/scopes.ts`, `apps/web/utils/rule/consts.ts`, `apps/web/app/(app)/[emailAccountId]/onboarding/onboardingFlow.ts`, `.../onboarding/StepDraft.tsx`, `apps/web/.env.example`
- Third party (biased, competitor): https://www.thisandthat.chat/blog/inbox-zero-review-2026 ; Inbox Zero's own blog https://www.getinboxzero.com/blog/post/soc-2-compliant-email-tools
