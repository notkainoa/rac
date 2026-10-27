# 04. Data, storage, import, and sync

## In plain English (at most 200 words)

Arc closes on 2026-12-22. An Arc user who opens rac today gets an empty sidebar and has to sign in everywhere again. This plan fixes that first. rac will read Arc's files on the Mac and rebuild each Arc space as a rac space. Each space keeps its name, emoji, colors, pinned tabs, folders, and open tabs. Favorites come over too. Next, rac brings your sign-ins (cookies), so sites stay logged in. Dia comes next, then Chrome, Safari, Zen, and Firefox.

Saved passwords need a choice. Helium turns off the browser's password manager, so rac has nowhere to keep them. The plan hands them to Apple Passwords or 1Password instead.

Behind the scenes, rac gets safer with your data. It keeps daily backups of your spaces, and any import can be undone. AI chats are stored encrypted instead of as plain text.

Later, a space can get its own sign-ins, like Arc profiles. Work and personal Google accounts can then sit side by side in one window. Sync comes after the release. It writes locked files to your own iCloud Drive, so no rac server is involved.

## What you need to decide

1. **04-D1. What does the first Arc import bring?** Sidebar only / sidebar plus sign-ins / everything including passwords. **Recommended: the sidebar first (by about 2026-11-17), then sign-ins (by about 2026-12-01). Both ship before Arc closes.**
2. **04-D2. Where do imported passwords go?** Hand them to Apple Passwords or 1Password / turn Chromium's password manager back on / skip them. **Recommended: hand them off through a short-lived file that rac deletes.**
3. **04-D3. How do Arc profiles map?** One shared sign-in jar / separate sign-ins per space / each becomes a rac profile (as Ardia does). **Recommended: separate sign-ins per space once built. Until then, bring only the main Arc profile's sign-ins.**
4. **04-D4. Build separate sign-ins per space?** Storage partition per space, opt-in / full profile per space / not now. **Recommended: opt-in partition, with one "identity" that several spaces can share.**
5. **04-D5. How are AI chats and agent run logs stored?** Plain JSON as today / encrypted JSON / encrypted SQLite with retention. **Recommended: encrypted SQLite. Chats stay until deleted. Runs are kept 30 days.**
6. **04-D6. How much backup?** `.bak` only / daily snapshots plus one before every import or migration / the same plus a Restore item in Settings. **Recommended: the last option, keeping 14 daily snapshots.**
7. **04-D7. Moving to another Mac before sync exists?** An Export/Import file / nothing. **Recommended: an export file in the first release after Arc import.**
8. **04-D8. Which sync?** None / an end-to-end encrypted folder (iCloud Drive by default, any folder for self-hosting) / wait for Helium's vault / a rac server. **Recommended: no sync in the first release. Build folder sync in phase 6. Use Helium's vault for Chromium data if it ships.**
9. **04-D9. Where does sidebar data live long term?** Keep it in Chromium's `Preferences` / move it to a rac-owned versioned file. **Recommended: keep it for now. Move it when sync work starts.**

## Where we are today

All FACT unless tagged. Paths are in the rac worktree or in the built tree at `/Users/knewton/Dev/Github/rac/build/src` (marked `CR:`).

**Where each kind of data lives now.**

| Data | Where | Format | Source |
|---|---|---|---|
| Spaces: id, name, emoji, theme, last active | Profile pref `rac.spaces` | JSON inside `Preferences`, plaintext. Unknown fields are kept for newer builds | `CR:chrome/browser/rac/spaces/space.h:22-80`; `plans/research/rac-baseline.md:323` |
| Themes | Inside each space (`SpaceTheme`: two color stops plus mode; 8 presets; custom colors allowed) | Same | `CR:chrome/browser/rac/spaces/space.h:22-43` |
| Hidden spaces' tabs | `<profile>/rac spaces`, plus `rac spaces.bak` | JSON, `kVersion = 1`, atomic, 1 s coalesce, background sequence | `CR:chrome/browser/rac/spaces/spaces_store.h:64-74`; `spaces_store.cc:58,257,271` |
| Favorites, pinned tabs, folders (one level), pinned URLs, names | Profile pref `rac.sidebar.lists` (`pinned.<space id>`) | JSON in `Preferences` | `CR:chrome/browser/ui/rac/sidebar/sidebar_items.cc:32`; `docs/internals/pinned-tabs.md` |
| Which space a window shows; tab-to-space and tab-to-item tags | Chromium session files (extra data) | Session format | `docs/internals/pinned-tabs.md` ("A space tag lives in two places") |
| Agent per-site rules; permission level | Prefs `rac.ai.agent_site_rules`, `rac.ai.agent_permission_level` | JSON in `Preferences` | `patches/rac/agent/14-site-rules.patch:598-603`; `13-permission-levels.patch:573-579` |
| Site controls (permissions, cookies) | Chromium content settings | Chromium's | `plans/research/matrices/features.md` (Per-site tools) |
| Settings | `rac.*` profile prefs; `rac.browser_updates` in Local State | JSON | `plans/research/rac-baseline.md:325-326` |
| One-time migrations | Two booleans: `rac.sidebar.migrated_pinned_tabs`, `rac.browser.center_address_bar_contents_migrated` | Prefs | grep of `patches/rac` |
| AI provider keys | Pref `rac.ai.encrypted_keys` | `os_crypt_async` ciphertext; Keychain item "rac Storage Key" | `CR:chrome/browser/rac/ai/ai_prefs.h:24-26`; `rac-baseline.md:328` |
| AI conversations | `<profile>/rac_ai_history.json` | **Plaintext JSON**, 16 MB read cap, saving on by default | `rac-baseline.md:329` |
| Agent run logs | Not stored as a separate log | n/a | `rac-baseline.md:319-334` (no row); `matrices/architecture-and-storage.md:173` |
| Cookies, history, extensions, bookmarks | Chromium's own SQLite and JSON | Chromium's | `rac-baseline.md:321` |

**Facts that shape this plan.**

- rac has no SQLite database of its own (FACT, `rac-baseline.md:321`).
- If `Preferences` is corrupt, Chromium renames it to `Preferences.bad` and starts with defaults (FACT, `CR:components/prefs/json_pref_store.cc:55-58,141`). Spaces, pins, and favorites live there, and no `.bak` covers them. INFERENCE: one bad write today loses a user's whole sidebar.
- Import is Helium's. Helium finds Arc and Dia profiles (`CR:chrome/browser/importer/chrome_importer_list.cc:86-95`). It imports bookmarks, history, and extensions (`CR:chrome/common/importer/chrome_importer_utils.cc:192-226`). Its `ArcSidebarImporter` turns Top Apps into bookmark-bar entries, and each space's pinned tabs into bookmarks in a folder named by the space's internal id (`CR:chrome/utility/importer/arc_sidebar_importer.cc:268-330`). It runs in the utility process and can only return bookmarks through the importer bridge (FACT, same file, `bridge_->AddBookmarks`).
- Helium strips passwords and autofill from every source (`CR:chrome/browser/importer/importer_list.cc:257-260`). Cookies are "Not supported yet" in Chromium's importer (`CR:components/user_data_importer/common/importer_data_types.h:27`).
- Helium forces the password manager off by policy (`helium-chromium/patches/helium/hop/disable-password-manager.patch`).
- rac's onboarding has an import screen that calls Helium's `listImportableProfiles` and `importProfile` (`patches/rac/onboarding/03-tour-window.patch:24-28`).
- Helium already keeps a denied Keychain from wiping data (`patches/helium/macos/prevent-reset-on-keychain-unavailability.patch`). Ardia found a second path: the item is briefly missing at login, and Chromium writes a new key (`plans/research/digests/ardia.md:223-230`). Whether Helium's patch covers that case is unverified.
- Chromium can isolate cookies per space. It has `SiteInstance::CreateForFixedStoragePartition` (`CR:content/public/browser/site_instance.h:255`; `plans/research/digests/long-tail.md:23`).
- Chromium has versioned SQLite migrations built in (`CR:sql/meta_table.h:75,122`).

## What others do

Full comparison: `plans/research/matrices/architecture-and-storage.md` (Matrix B) and `plans/research/matrices/features.md` (Import, Sync and backup).

- **Cra** stores everything as plain JSON files, debounced at 0.4 s, with one `.bak` each. It also runs a repair pass at every launch. Its Arc import is the most exact in the field: sidebar, favicons, archive, windows, link routing, and Arc's Chromium profile. It re-encrypts passwords and cookies with its own key and stages them in a 0600 file. It writes them at next launch, before Chromium opens its databases. Spaces with the same title merge, so a rerun is safe (`digests/cra.md`; `research/cra.md:375-432,604-637`).
- **Ardia** imports Arc spaces, pins, folders, live folders, splits, and themes. It turns each space into a profile, which loses shared logins (issue #50). It syncs through sealed files in iCloud Drive, with no server and no account. Its two-Mac test was never run (`digests/ardia.md:67-86,231-236`).
- **Helium** has the bookmark-only Arc importer above. Its experimental "private vault" sync is off by default. It needs a provider extension to store encrypted blobs, and it carries Chromium data types, including `PREFERENCES` (`digests/helium.md:111-112`; `/tmp/rac-overhaul/src/helium/patches/helium/core/sync/datatype-policy.patch:19-30`).
- **Zen** keeps 3-hour backup buckets, the newest 20, but tries only two fallbacks. Its storage moves were followed by data-loss reports (`digests/zen.md`, Avoid 8).
- **Nook** keeps daily dated backups for 7 days, a `formatVersion`, 30-day tombstones, and fractional ordering (`matrices/architecture-and-storage.md:29-33`).
- **T3 Code** shows the trap: an event log reached 17-40 GB. It also snapshots its database before an update and rolls back if the trial fails (`digests/t3code.md:86-98`).
- **Stedding and Brave** isolate cookies per space or container with a storage partition. Stedding needs one upstream hunk. Brave keeps the partition through session restore with a URL prefix (`digests/long-tail.md:20-25`).
- **Crest** keeps one SQLite file of JSON records and offers optional CloudKit sync. Passwords never enter that sync. Its portable archive leaves out passwords, cookies, and site storage (`digests/long-tail.md:47`).

## Options

Each option is a whole strategy for this area. Sign-ins per space and sync have their own sub-choices (04-D4, 04-D8). Those are covered inside Option B.

### Option A: Ship-first. Arc sidebar import on today's stores, nothing else

rac gains an Arc importer that writes into the existing spaces and sidebar services. Nothing else changes before Arc closes. Backups, encryption, sign-ins, and sync wait.

- **Details.** A rac-owned reader in `chrome/browser/rac/import/` parses `StorableSidebar.json`. An applier calls `SpacesService` and `SidebarItems`. Helium's importer still brings history and extensions.
- **Pros.** Smallest change. About 3-5 upstream hunks. Lands well before 2026-12-22.
- **Cons.** Users still sign in everywhere again. An import goes into a sidebar that has no backup and no undo. Chat history stays plaintext.
- **Effort.** M, about 7-9 agent-days.
- **Risk.** Low for code. Medium for trust: a bad first import with no way back.
- **Locks in.** Nothing.

### Option B: Local-first foundation (recommended)

rac first adds a safety net: daily backups, versioned data, and undo for imports. Then it builds Arc import in two cuts, sidebar first and sign-ins second. After the release, AI data moves to an encrypted store and spaces can get their own sign-ins. Sync is designed now but built later, as sealed files in a folder the user owns.

- **Details.** Milestones M0-M6 below. Settings and the sidebar stay in prefs for now (04-D9). Data that grows without limit goes to SQLite with retention: AI chats, agent runs, and later the archive. Small, bounded data stays in prefs or JSON. Every importer writes through service APIs, so storage can change later without touching importers.
- **Sign-ins per space (04-D4).** (B1) A storage partition per space, opt-in, as Stedding and Brave do. (B2) A full Chromium profile per space in one window, as Arc and Crest do; L+ effort, and it fights rac's one-sidebar-per-profile model. (B3) Not now; profiles stay one per window. Pick B1.
- **Sync (04-D8).** (S1) None. (S2) Sealed-folder sync, as Ardia does: iCloud Drive by default; Syncthing, Dropbox, or a NAS for self-hosting. (S3) Helium's vault, once Helium ships it. (S4) A rac server: rejected, because it breaks "no rac servers". Pick S1 now, then S2 for rac's sidebar data. Take S3 for Chromium data (bookmarks, history) if Helium ships it.
- **Pros.** Arc users get spaces and sign-ins before the shutdown. Every import can be undone. Chat history stops being plaintext. Per-space sign-ins fix Arc's profile model properly, which Ardia gets wrong.
- **Cons.** More work before Arc closes than Option A. The partition hook sits in `browser_navigator.cc`, a file three other patches already edit (`digests/long-tail.md:25`).
- **Effort.** Before 2026-12-22: M0-M2, about 17-22 agent-days in two parallel worktrees. After: M3-M5, about 20-30 agent-days. Sync (M6): L, about 20-35 agent-days.
- **Risk.** Medium. Keychain prompts, macOS data-access prompts, and Arc format variants need care.
- **Locks in.** A record shape (stable id, timestamps, source id) that later sync must honor. That is cheap and reversible.

### Option C: Sync-first rebuild. One rac store now

All rac data moves out of `Preferences` into one rac-owned SQLite file of records, like Crest's. Import writes into it, and iCloud folder sync follows soon after.

- **Details.** New `RacStore` service. Spaces, pins, favorites, themes, rules, archive, and AI data become rows. Every record gets an id, a hybrid logical clock, and a tombstone. The settings WebUI reads through a new handler instead of prefs.
- **Pros.** The cleanest base for sync. One backup target. One migration system.
- **Cons.** It rewrites the spaces and pinned stores that 44 patches depend on (26 spaces, 18 pinned; `rac-baseline.md`), before Arc closes. Settings lose free pref binding. It is the classic moment for data loss (Zen's history).
- **Effort.** L-XL, about 30-45 agent-days before import even starts.
- **Risk.** High. It misses the Arc window.
- **Locks in.** A storage engine and a sync shape before anyone has asked for sync.

### Option D: Lean on Helium

rac extends Helium's own importer to map Arc data, and stores rac data as syncable prefs. It then waits for Helium's vault sync.

- **Details.** Subclass `ArcSidebarImporter` (Helium made `ImportBookmarks` virtual; `digests/helium.md`, take 6). New bridge methods would carry spaces from the utility process. rac prefs would be registered as syncable, with entries in `chrome_syncable_prefs_database.cc`.
- **Pros.** Reuses Helium's process model and its UI. Sync costs rac little if Helium ships it.
- **Cons.** Spaces cannot cross the importer bridge without editing Helium- and Brave-created files, which AGENTS.md says to avoid. Chromium syncs a dictionary pref as one value, so two Macs editing the sidebar would overwrite each other (INFERENCE). There is no shipping date for Helium's sync (`digests/helium.md`, Open questions). Its storage provider must be an extension (`provider/api.patch`).
- **Effort.** M for import, though with high rebase cost. Sync timing is unknown.
- **Risk.** High dependency risk.
- **Locks in.** Helium's timeline, and edits to Helium's importer files.

### Recommendation

**Option B.** It is the only option that brings both spaces and sign-ins before Arc closes, with a way back if an import goes wrong. Take from A the rule that import ships first, on today's stores. Take from C the record shape (stable ids, source ids, timestamps), adding it as fields, not as a rewrite. Take from D the detection code, the history and extension import, the macOS permission prompt, and the vault for Chromium data later. Do not route rac data through it.

## Recommended plan

Dates assume work starts 2026-10-28. Arc import is only useful inside a signed release, so M1 and M2 depend on plan 06 shipping one.

### M0. Safety net (target 2026-11-04; S-M, 4-5 agent-days)

**Goal.** No rac data can be lost silently, and every later change can be undone.

**Tasks.**
1. Add `rac::DataBackups`, a rac-owned profile service. Once a day, on the first change, it writes one snapshot to `<profile>/rac backups/YYYY-MM-DD.json`. The snapshot holds `rac.spaces`, `rac.sidebar.lists`, the agent rules, and the `rac spaces` file. It keeps the newest 14. It also writes a named snapshot before any import or migration. Writes run on a background sequence with `ImportantFileWriter`. Files are mode 0600.
2. Recovery order at load: the live data, then `.bak`, then the newest dated snapshot, then older ones. This fixes Zen's two-fallback limit. If `Preferences.bad` exists and `rac.spaces` is empty, offer "Restore your spaces from <date>". Never restore silently.
3. Replace the two migration booleans with one integer pref, `rac.data_version`. A small runner applies numbered, idempotent steps, after a snapshot. Keep the old booleans readable for one release.
4. Versioning rules for every rac file, written in `docs/internals/storage.md`. Each file carries a `version` and a `min_reader_version`. Builds keep unknown fields, as `Space` and `StoredSpace` already do. A build refuses to write a file whose `min_reader_version` is newer than itself. SQLite stores use `sql::MetaTable` with compatible-version numbers.
5. Check the Keychain "no silent reset" case. Read Ardia's patch notes (`research/ardia.md:546-553`) against Helium's patch. Add a test only if the gap is real.
6. Add a dev-only switch, `--rac-import-source-root=<dir>`, so tests read copies, never real Arc data. Leave it out of release builds (`rac-baseline.md`, take 12).

**Acceptance.** Corrupting `Preferences` in a test profile restores spaces and pins after one confirmation. Snapshots stay at 14 or fewer. A cold start reads nothing extra when the live data is fine.

**Verification.** Unit tests for snapshot rotation, recovery order, and the migration runner. A screenshot of the restore prompt in light and dark mode. A trace showing no extra disk read at startup.

**Patch surface.** New files in `chrome/browser/rac/storage/`. Hooks: one keyed-service factory registration and one `BUILD.gn` dependency. About 2-3 upstream hunks (INFERENCE).

### M1. Arc import, sidebar (target 2026-11-17; M, 7-9 agent-days)

**Goal.** An Arc user sees their spaces in rac within a minute, looking like Arc.

**Tasks.**
1. **Reader** (`chrome/browser/rac/import/arc_reader.{h,cc}`). It is pure parsing, with no browser state, so fixtures can test it. It reads `StorableSidebar.json` using Cra's exact keys (`research/cra.md:604-627`): the flat `[id, object, …]` lists; `containerIDs` (`pinned`, `unpinned`); `topApps` containers; space `title` and `profile`; `customInfo.iconType.emoji_v2` or `.emoji`; `windowTheme` gradients; and dates counted in seconds since 2001. It also reads favicons from `SidebarItemsFaviconCache/<md5(id)>`. Parsing uses `base::JSONReader` on a background thread.
2. **Import plan** (`import_plan.h`). A source-neutral tree, like Cra's `ImportPlan`: spaces, favorites, pinned trees, open tabs, theme, emoji, and source ids. Every later importer (Dia, Zen, Safari) produces the same plan.
3. **Mapping.**
   - Arc space → rac space, with name, emoji, and theme. The first two gradient base colors become `color1` and `color2`. The light and dark variants become the mode.
   - Pinned container → the space's pinned list.
   - Arc allows nested folders; rac folders are one level deep (`docs/internals/pinned-tabs.md`). Deeper levels flatten into their top folder as "Parent › Child" names.
   - Split views and tab groups flatten to tabs (as Cra does).
   - Unpinned tabs → that space's open tabs, stored unloaded in the `rac spaces` file. A checkbox shows the count.
   - Top Apps from the main Arc profile → rac favorites.
   - Top Apps from other Arc profiles → a "Favorites" folder pinned in each space that uses that profile. Then a work favorite never opens with the personal sign-in.
   - Favicons → Chromium's favicon database, so unloaded pins show icons with no network request.
4. **Applier** (`import_applier.cc`). It writes only through `SpacesService` and `SidebarItems`. It runs after an M0 snapshot. Each created item records its Arc source id, so a rerun skips what already exists. That is exact where Cra's title match is not.
5. **Helium's part.** Run Helium's importer for history and extensions, with bookmarks turned off for Arc. Otherwise pins arrive twice, as bookmarks too.
6. **Undo.** "Undo Arc import" in Settings, for 7 days. It restores the pre-import snapshot and removes the created items. A space the user has changed since asks first.
7. **Not imported, and said so in the summary:** archive (rac has none yet), link routing rules (kept raw in `<profile>/rac imports/` for plan 07's Air Traffic Control), Boosts, Easels, Notes, and live folders.
8. **UI.** One import sheet, reached from onboarding's import step and from Settings. Plan 01 owns the look. Before the macOS data-access prompt, rac explains it. On macOS 27, reuse Helium's Files & Folders prompt (`research/helium.md:101`).

**Acceptance.** Fixtures from at least three Arc layouts import with correct names, emoji, colors, folders, and order: one space, several spaces across two profiles, and nested folders with splits. A second run adds nothing. Undo restores the exact prior state. The import makes zero network requests.

**Verification.** Reader unit tests with fixtures. A browser test for the applier and for undo. Screenshots before and after (empty sidebar, then imported spaces) in light and dark, with the address bar in the toolbar and in the sidebar. A short video of the import sheet, progress, and summary. A net-log run proving no network requests.

**Patch surface.** New files only, plus hooks: `BUILD.gn`, rac's onboarding handler (rac-owned), and one call to deselect bookmarks for Arc. About 2-4 upstream hunks (INFERENCE). No edits to Helium's importer files.

### M2. Arc sign-ins, password hand-off, Dia (target 2026-12-01; M, 6-8 agent-days)

**Goal.** Sites stay signed in after the move. Passwords reach a real password manager. Dia users get the same flow.

**Tasks.**
1. **Credential reader** (`credential_reader_mac.mm`). It asks the Keychain for "Arc Safe Storage" (account "Arc") only after the user clicks "Unlock Arc data". It copies `Cookies` and `Login Data` with their `-wal` and `-shm` files to a temp folder, opens the copy with `sql::Database`, and decrypts the `v10` values. The scheme is PBKDF2-SHA1 ("saltysalt", 1003 rounds) with AES-128-CBC. It checks padding, because a wrong key passes about once in 256 tries. It strips the SHA-256 host prefix from cookie databases at version 24 and up. Source: Cra's `CredentialImport.swift`, MIT, ported with credit.
2. **Cookie writer.** It writes through `CookieManager::SetCanonicalCookie` on the profile's storage partition while rac runs. Chromium re-encrypts with "rac Storage Key". INFERENCE: because rac is Chromium, it needs no Cra-style staging file and no restart.
3. **Scope until M4.** Only the main Arc profile's cookies come over, because two profiles' cookies would collide in one jar. The summary says: "Sign-ins for 'Work' arrive when separate sign-ins ship." The import record keeps the space-to-Arc-profile mapping so M4 can finish the job.
4. **Password hand-off (04-D2).** "Move passwords to…" offers Apple Passwords and 1Password. rac writes a CSV into a 0700 temp folder and opens the target app's import. It deletes the file when import is confirmed, after 10 minutes, or at quit. rac keeps no passwords.
5. **Dia.** Dia's Chromium profiles use "Dia Safe Storage". Read `StorableProfileContainers.json` for open tabs and `User Data/*/Bookmarks` for Dia's imported Arc folders (Cra's `DiaImporter`). Dia's pinned tabs live in an SQLCipher `tabs.db` that nobody has read (`digests/ardia.md:78`). Try Dia's AppleScript dictionary for pinned tabs, as Ardia does. Each Dia profile maps like an Arc profile.

**Acceptance.** After importing a fixture profile, a test site's session cookie works in rac. Denying the Keychain prompt leaves the sidebar import intact and shows a calm retry. No plaintext secret remains on disk after the hand-off.

**Verification.** Unit tests: decrypting fixtures, the version-24 prefix, wrong-key rejection. A browser test that a cookie is set and sent. Screenshots of the unlock explanation, the Keychain prompt state, and the summary. A video of the password hand-off.

**Patch surface.** New files. Possibly one upstream hunk to reach the cookie manager from rac's service (INFERENCE).

### M3. Encrypted AI store (target 2026-12-15, parallel to M1-M2; S-M, 4-6 agent-days)

**Goal.** Chats and agent history are encrypted at rest, bounded, and cost nothing with AI off.

**Tasks.**
1. `<profile>/rac_ai.db` through Chromium's `sql::Database`, in WAL mode, versioned with `sql::MetaTable`. Tables: `conversations` (id, title, updated); `messages` (conversation, role, encrypted text); `runs` (id, conversation, started, ended, outcome, agent, level); and `tool_calls` (run, tool, origin, decision, encrypted arguments and result, error). One row per run and per tool call, never per token (`digests/local-first-and-sidecars.md`, take 5).
2. Text columns are encrypted with `os_crypt_async`, the same path as the API keys (`rac-baseline.md`, take 9).
3. Retention: conversations stay until the user deletes them, or turns off "Save history". Runs and tool calls are kept 30 days. The run table doubles as the agent's audit log for plan 05.
4. Migrate `rac_ai_history.json` once, then delete it.
5. The store is created only when AI is on, following the existing rule (`docs/internals/ai.md`, "AI off costs nothing").

**Acceptance.** No plaintext chat text in the profile folder. A fresh profile with AI off has no `rac_ai.db`. The database stays bounded on a 30-day synthetic run load.

**Verification.** Unit tests for migration, retention, and encryption round-trips. A `strings` check on the database file. An AI-off check in a fresh profile.

**Patch surface.** rac-owned files only. 0-1 upstream hunks.

### M4. Separate sign-ins per space (target late January 2027; M-L, 10-15 agent-days)

**Goal.** A space can use its own accounts, as Arc profiles did. Arc users with several profiles get every sign-in.

**Tasks.**
1. **Model.** A profile-level list of identities, `rac.identities` (id, name, partition token). Each space gains an optional `identity_id`. Several spaces can share one identity, matching Arc profiles that served several spaces. Stedding binds one jar per space and calls sharing "a later ADR" (`/tmp/rac-overhaul/src/stedding/docs/decisions/0019-space-sessions-are-storage-partitions.md`).
2. **Partition.** Tabs in such a space open with `CreateForFixedStoragePartition` against `StoragePartitionConfig::Create(profile, "rac", <token>, false)`. Make this one hook in `browser_navigator.cc`, which already picks the `SiteInstance`. Turning isolation off keeps the jar for later (Stedding).
3. **Restore.** rac already saves each tab's space in session extra data (`docs/internals/pinned-tabs.md`). So restore can rebuild the partition from the space, instead of Brave's URL prefix. This needs hooks in session restore and Reopen Closed Tab, plus rac's own hidden-space restore. Test discard too.
4. **Moving a tab** to a space with another identity reopens its URL in the target jar. The page state is lost, and the user is told quietly.
5. **Favorites** stay on the default jar. The M1 rule already keeps other identities' favorites inside their spaces.
6. **Finish Arc and Dia.** Re-run sign-in import for each extra Arc or Dia profile into its identity.
7. **Agent.** A "clean room" identity with no sign-ins, for plan 05 (`digests/long-tail.md`, agent idea B5).
8. **Known limit.** `chrome.cookies` without a partition sees only the default jar. Cookie extensions miss isolated spaces (Stedding ADR 0019).

**Acceptance.** Two spaces are signed into two Google accounts at once, and both survive a restart, Reopen Closed Tab, and unloading. With no isolated spaces, navigation cost is unchanged.

**Verification.** Browser tests for restart and restore. Screenshots of two spaces showing different accounts, the space edit toggle, and incognito unchanged. A video of switching spaces. Before and after timing of the navigation path.

**Patch surface.** About 3-5 upstream hunks: navigator, session restore, tab restore, and possibly `web_contents_impl.cc` if a leak shows up (INFERENCE). This is the riskiest rebase item in the plan.

### M5. Export file and more importers (target February 2027; M, 6-10 agent-days)

**Tasks.**
1. **"Export rac setup…"** writes a `.rac` file (JSON, `format: "rac-export"`, `version: 1`). It holds spaces, themes, identities (names only), pins, favorites, folders, agent site rules, and a list of rac settings. It never holds cookies, passwords, history, keys, or chats. "Import rac setup…" merges by stable id and never closes an open tab (`digests/long-tail.md`, take 3). The same record shape becomes the sync payload in M6.
2. **Zen.** Spaces, Essentials, pinned tabs, and folders from `zen-sessions.jsonlz4`, with older profiles in `places.sqlite` (Cra's `ZenImporter.swift`). Containers map to identities. Firefox cookies are plain SQLite.
3. **Safari.** Use Safari's "Export Browsing Data" zip (Bookmarks, History, Passwords.csv), as Cra does. This avoids asking for Full Disk Access. Passwords go to the M2 hand-off.
4. **Chrome and other Chromium browsers.** Helium already does bookmarks, history, and extensions. Add cookies through the M2 reader ("Chrome Safe Storage" and similar).
5. **Firefox.** Helium's importer, plus cookies.

**Verification.** Fixture tests per source. Screenshots of each source in the import sheet.

**Patch surface.** New files only.

### M6. Sync (phase 6, only after maintainer approval; L, 20-35 agent-days)

**Goal.** The sidebar and rac settings follow the user between their Macs, with no rac server.

**Tasks.**
1. **Move the data first (04-D9).** Spaces, pins, favorites, and identities move from prefs into a rac-owned document of records. Each record has an id, a hybrid logical clock, a device, a tombstone, and a fractional position. M0 snapshots run before the move.
2. **Seal files, Ardia's way.** A 24-word phrase holds 256 bits. HKDF yields an AES-256-GCM file key and an HMAC name key. Additional authenticated data binds each file to its path. Files are padded to 1 KiB and never compressed. They are immutable, saved under random names, and moved in with `NSFileCoordinator`. Merges are per-record last-writer-wins. Snapshots compact old files, and tombstones expire after 45 days (`research/ardia.md:370-389`).
3. **Where the files go.** `~/Library/Mobile Documents/com~apple~CloudDocs/rac Sync/` by default, or any folder. Syncthing, Dropbox, or a NAS makes this the self-hosted option.
4. **The key.** Keychain item "rac Sync Key", this device only. The phrase pairs a second Mac.
5. **Scope v1.** Sidebar, themes, identities (names only), agent site rules, and chosen settings. Not synced: cookies, passwords, history, open tabs, chats. Chromium data can ride Helium's vault later, if Helium ships it.
6. **Lazy.** Nothing runs until sync is turned on. Then it checks on change and every few minutes, not Ardia's 15 s.

**Acceptance.** A real two-Mac test over iCloud Drive (Ardia never ran one): concurrent edits, offline edits, deletes, and recovery from a lost phrase.

**Patch surface.** rac-owned files, in the browser process (03-D1).

### Where each kind of data will live

| Data | Lives in | Encrypted | Backed up | Synced (M6) |
|---|---|---|---|---|
| Spaces, themes, identities | `rac.spaces`, `rac.identities` prefs; a rac document from M6 | No (FileVault) | Daily | Yes |
| Pins, favorites, folders | `rac.sidebar.lists`; a rac document from M6 | No | Daily | Yes |
| Hidden spaces' tabs | `<profile>/rac spaces` | No | Daily | No |
| Agent per-site rules, level | `rac.ai.*` prefs | No | Daily | Yes |
| Link routing, Boosts (plans 07) | Prefs if small; rac document if large | No | Daily | Yes |
| Archive (if approved, plan 07) | SQLite with retention | Text, yes | No | No |
| AI chats, agent runs | `<profile>/rac_ai.db` | Text, yes | No | No |
| API keys | `rac.ai.encrypted_keys` | Yes | No | No |
| Cookies per identity | Chromium storage partitions | Chromium's | No | No |
| Import records | `<profile>/rac imports/` (0600) | No secrets inside | n/a | No |
| Settings | `rac.*` prefs, Local State | No | Selected | Selected |

## Fit with the non-negotiables

- **Private.** Every import reads local files and makes no network request; favicons come from Arc's cache. Export files never contain secrets. Sync is end to end, to the user's own folder, and rac runs no server. **Bent:** the password hand-off writes plaintext passwords to a 0700 temp file for a few minutes. The alternative is a rac password manager, which Helium deliberately turns off. Flagged for 04-D2.
- **Never slower than Helium.** Backups write once a day on a background sequence. Startup reads a backup only when live data fails. A partition costs nothing until a space is isolated: the navigator hook checks one field. Each isolated identity adds its own network context and cache (INFERENCE: a few MB each). Measure this in M4.
- **AI off costs nothing.** `rac_ai.db` exists only with AI on. Backups and import never touch AI data.
- **Cheap to update.** Nearly everything is in new rac-owned files. Upstream hunks: M0-M2 about 5-8, M4 about 3-5. **Bent:** M4 adds a hunk to `browser_navigator.cc`, a hot file, and to session restore. These are the costliest lines in this plan. No Helium importer files are edited.
- **Calm UI.** One import sheet, plain progress, a summary of what came and what didn't, and Undo. The Keychain and macOS prompts are explained before they appear.
- **GPL.** Ports from Cra (MIT) and Ardia's own files (Apache-2.0) keep their notices (`digests/ardia.md:215-217`). Stedding (BSD-3) and Brave (MPL-2.0) inform the design only. Reading Arc's file format is fine. Do not copy Arc's text or assets (`digests/cra.md`, Avoid 5).

## Dependencies on other plans

- **01 ui-shell.** The import sheet in onboarding and Settings, the restore prompt, Undo import, the "Separate sign-ins" toggle in space editing, and whether rac allows nested folders (M1 flattens them).
- **02 visual-design-and-motion.** How Arc's gradients and noise map onto rac themes. Calm motion for import progress, honoring Reduce Motion.
- **03 core-architecture.** This plan follows 03-D1 and 03-D2: every store lives in the browser process as a profile service, with no resident helper. 03's placement table puts history in browser-process SQLite and sync in the browser as sealed files in a user folder; plan 04 owns their schema, retention, migration, backups, and sync files (`plans/03-core-architecture.md`, M5 and the placement table). Importers stay in the browser too, because cookies must be written through Chromium. If 03-D2 ever approves a helper, `rac_ai.db` and the sync engine sit behind one interface so they can move. If 03-D8 moves rac sources into an overlay folder, the new `storage/` and `import/` directories move with it.
- **05 agents-and-ai.** The `runs` and `tool_calls` schema is the agent audit log. Plan 05 sets retention and what an outside agent may read. The clean-room identity (M4) serves agents without sign-ins.
- **06 engineering-and-shipping.** M1 and M2 matter only inside a signed release before 2026-12-22. CI must run the reader fixture tests. A release smoke test should carry real data from the previous build (Ardia's pattern), covering migrations.
- **07 power-features.** Archive storage, Air Traffic Control using the imported link rules, Boosts storage, and Little Arc.

## Risks and unknowns

- **Testing on real Arc data.** AGENTS.md forbids pointing builds at real rac or Helium profiles. Reading the maintainer's real Arc folder is not covered by that rule, but it is close. The plan uses fixtures and copies, through the dev switch. Running against a live Arc install needs maintainer sign-off.
- **Arc format variants.** Only Cra's and Helium's readings are known. Old Arc versions, empty profiles, and odd shapes such as emoji code points need fixtures. Arc may stop launching after 2026-12-22, but its files stay on disk (INFERENCE), so import stays possible later.
- **macOS prompts.** The App Data protection prompt and the Keychain prompt may confuse users or be denied. Whether macOS 27's gate covers Arc's folder is unverified (`digests/helium.md`, Open questions).
- **Cookie schema drift.** Cookie database versions differ across Chromium releases (the v24 host prefix). Map columns by name, as Cra does.
- **Partition leaks** through restore, discard, downloads, service workers, extensions, or `window.open`. Brave patches `web_contents_impl.cc` for this; Stedding does not, yet.
- **Keychain silent reset.** If the "rac Storage Key" item is replaced, cookies and API keys become unreadable. M0 checks this path.
- **Helium sync** has no date, and it may never carry rac's data.
- **Two-Mac sync** is untested anywhere in the field.
- **Effort.** M0-M2 is about 17-22 agent-days in 56 days, alongside a first release and a Helium sync. It is tight but realistic only if M1 starts by early November.

## Open questions

1. Should imported cookies include known tracker domains, or only sites in the user's sidebar and history? Cra imports everything.
2. Does Arc's `profile` field name readable profile titles for the summary, or only ids?
3. Should Dia's pinned tabs come through AppleScript (Dia must be running), or wait for someone to read `tabs.db`?
4. Is a 7-day Undo window right, or should Undo stay until the next import?
5. Should agent site rules sync (M6), given they are security decisions made on one Mac?
6. Should the sync key also live in iCloud Keychain, so a second Mac needs no phrase? That needs a team ID and access groups; `MAC_TEAM_ID` is empty today (`rac-baseline.md:333`).
7. Should chats ever sync, end to end, as an opt-in?
8. Does Helium's Keychain patch already cover Ardia's login-time case?
9. Should an Arc profile with its own spaces become a rac identity (this plan) or a rac profile window? This plan assumes identity, against Ardia's choice.

## Draft thread brief (DRAFT; not to launch until the maintainer approves)

> **DRAFT. Do not launch until the maintainer approves plan 04.**
>
> **Thread:** architecture and backend, "Data and import". Model: Opus for M0, M2, and M4. Sonnet may do the M1 reader and fixtures under review.
>
> **Goal:** Ship M0 (safety net), M1 (Arc sidebar import), and M2 (Arc sign-ins, password hand-off, Dia) in signed releases before 2026-12-22. Then M3 (encrypted AI store) and M4 (separate sign-ins per space). M5 and M6 wait for a new go-ahead.
>
> **Read first:** `AGENTS.md`, `VISION.md`, `plans/04-data-storage-import-sync.md`, `docs/internals/pinned-tabs.md`, `docs/internals/ai.md` ("AI off costs nothing"), `plans/research/cra.md:375-432,604-637`, `/tmp/rac-overhaul/src/cra/Sources/Cra/Services/Import/` (MIT; port with credit), `CR:chrome/utility/importer/arc_sidebar_importer.cc`, and the Stedding ADR 0019 path above.
>
> **Rules:** one worktree per milestone. Put code in `chrome/browser/rac/storage/` and `chrome/browser/rac/import/`. Upstream edits stay small hooks; report the hunk count in each PR. Never edit Helium's importer or patch files. Never read real Arc, Dia, Helium, or rac profiles; use fixtures and `--rac-import-source-root`, kept out of release builds. Snapshot before every import or migration. The importer makes no network requests.
>
> **Done means:** fixture tests pass in CI. The import is idempotent and undoable. Screenshots cover the sidebar before and after import in light and dark, both address-bar placements, and incognito unchanged. Videos show the import sheet and the password hand-off. A net log shows zero requests during import. `he validate series` passes. Each PR states which "Cover every surface" items applied.
