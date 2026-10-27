# The action table (draft)

**Status: draft schema, nothing is built.** It is the contract for
`rac_actions.{h,cc}`, which plan 03 (M1) will write. The UI, guard, and
shortcut work all build on it, so change it here first.

One static list of everything rac can do. It is compiled-in data, with no
service and no startup cost. The sidebar, command bar, menus, shortcuts, the
built-in agent, and outside agents all read the same rows, so a feature is
written once and each surface only chooses whether to show it.

## The row

```cpp
namespace rac::actions {

enum class Surface { kSidebar, kCommandBar, kMenu, kShortcut,
                     kBuiltInAgent, kOutsideAgent };
using Surfaces = base::EnumSet<Surface, Surface::kSidebar, Surface::kOutsideAgent>;

// Same three values as today's agent::RiskClass in tool_registry.h.
enum class RiskClass { kNone, kLow, kConsequential };
// How an outside client is treated (plan 05's table). kNotOffered = no row
// reaches tools/list for outside clients.
enum class OutsideClass { kNotOffered, kRead, kFreeInOwnTabs, kAlwaysAsks };
// The four MCP annotation hints. The table always stores all four.
struct McpHints { bool read_only, destructive, idempotent, open_world; };
// kReadOnlyOnly is today's wire format: only {"readOnlyHint":true}, and only
// on read tools. kFull sends all four. The 15 current tools use kReadOnlyOnly.
enum class WireHints { kReadOnlyOnly, kFull };
enum class Dispatch { kBrowser, kAgentController };

struct Action {
  std::string_view id;           // Stable forever, never reused. Also the MCP tool name.
  int label_id;                  // IDS_ string: command bar and sidebar. 0 = not listed by name.
  int menu_label_id;             // Plan 07. 0 = same as label_id.
  std::string_view description;  // English, for tools/list only.
  std::string_view args_json;    // JSON Schema for the arguments, written out in full.
  ShortcutSpec default_shortcut; // Plan 07. {key, modifiers}; {} = none.
  Availability availability;     // Plan 07. What it needs (a tab, a web page, not incognito...).
  Surfaces surfaces;
  bool ai_only;                  // Cannot work without the assistant. Never shown with AI off.
  std::optional<RiskClass> risk;      // Plan 05's guard reads this.
  std::optional<OutsideClass> outside;  // Plan 05.
  std::optional<McpHints> hints;      // Unset until classified; a test fails on it.
  WireHints wire;
  Dispatch dispatch;
  Handler run;                   // Browser-side function. Null for kAgentController.
};

std::span<const Action> All();
const Action* Find(std::string_view id);
// The only way UI code walks the table. Drops ai_only rows when AI is off and,
// for the UI surfaces, rows whose availability fails, so no caller checks the
// AI switch itself.
std::vector<const Action*> ForSurface(Surface, const ActionContext&);
}
```

`args_json` is parsed with `base::JSONReader` and written back with
`base::JSONWriter`, which sorts keys, the same as today's `base::DictValue`
output. Every schema is written out in full, so an action with no arguments
carries today's empty object schema.

Rows live in per-group files joined by one central list in `rac_actions.cc`.
`GetToolDefinitions()` (and so `tools/list` and the direct loop) returns only
the rows with `dispatch == kAgentController`, in table order. Rows that
`run` in the browser reach the outside door through plan 05's routing, not
through the controller.

## First rows

The first 15 are today's agent tools. Their names, descriptions, and schemas
move over unchanged, and `tools/list` for them must stay byte-identical (a
golden-bytes test). They are `ai_only = false`, because an outside agent uses
them with AI off. They have no UI surface, so they never appear in the
command bar. Reads carry `readOnlyHint` on the wire and actions carry nothing,
as today. The stored hints below are what the actions really are, and plan 05
confirms them.

| id | Risk | Hints (RO, destructive, idempotent, open-world) | Surfaces | Outside |
| --- | --- | --- | --- | --- |
| `snapshot`, `get_page_text`, `find_in_page` | none | T, F, T, F | built-in, outside | read |
| `list_tabs` | none | T, F, T, F | built-in, outside | read (own and shared tabs) |
| `click`, `type`, `press_key` | low | F, T, F, T | built-in, outside | free in own tabs |
| `select_option` | low | F, T, T, T | built-in, outside | free in own tabs |
| `scroll` | low | F, F, F, F | built-in, outside | free in own tabs |
| `wait_for_settle` | low | F, F, T, F | built-in, outside | free in own tabs |
| `navigate` | consequential | F, F, T, T | built-in, outside | free in own tabs |
| `go_back`, `open_tab` | low | F, F, F, T | built-in, outside | free in own tabs |
| `switch_tab` | low | F, F, T, F | built-in, outside | free in own tabs |
| `close_tab` | low | F, T, T, F | built-in, outside | free in own tabs |

The runtime escalation in `ClassifyActionRisk` (risky targets, cross-origin,
`open_tab`) stays code, not table data.

New rows, from plan 05's non-page table and plans 01 and 07. All `kFull`.

| id | Risk | Hints | Surfaces | AI | Outside | Shortcut |
| --- | --- | --- | --- | --- | --- | --- |
| `list_spaces` | none | T, F, T, F | sidebar, outside | off ok | read | none |
| `reload` | low | F, F, T, F | menu, shortcut, command bar, built-in, outside | off ok | free in own tabs | Cmd+R (Chromium's) |
| `move_tab_to_space` | low | F, F, T, F | command bar, built-in, outside | off ok | always asks | none |
| `pin_tab` | low | F, F, T, F | sidebar, command bar, built-in, outside | off ok | always asks | plan 01 |
| `clear_tabs` | consequential | F, T, F, F | sidebar, command bar, shortcut | off ok | not offered | plan 01 |
| `copy_as_markdown` | none | F, F, T, F | menu, command bar, shortcut | off ok | not offered | Shift+Opt+Cmd+C |
| `ask` | none | F, F, F, T | command bar | **AI only** | not offered | none |

"Never" actions from plan 05 (change settings, site rules, or levels; install
extensions; clear history or data; delete a space) have no outside surface.
A test lists those names and fails if any gets one.

## Who reads it

- **Command bar (plan 01).** Calls `ForSurface(kCommandBar)`, filters and ranks
  the rows (plan 01 decides how), and runs `run` directly, one function
  call. With AI off, `ForSurface` has already dropped the Ask row and every
  AI label (ruling 16). Plan 01 may add rows and set `label_id` and the UI
  bits of `surfaces`. It never edits `risk`, `outside`, or `hints`.
- **Guard and MCP (plan 05).** `tools/list` is generated from rows that have
  `kOutsideAgent` or `kBuiltInAgent`. An unknown id is blocked, as today.
  The guard reads `risk` and `outside` in place of `default_risk` and
  `ToolKind`, which become views of the row. Plan 05 may add rows and set
  `risk`, `outside`, `hints`, `wire`, `args_json`, and the agent bits.
- **Shortcuts and labels (plan 07).** Helium's shortcut metadata reads
  `default_shortcut` and `menu_label_id` through one hook, replacing the
  per-command `case` hunks. Plan 07 may set only `default_shortcut`,
  `menu_label_id`, and `availability`, and must check each shortcut against
  Chromium's and Helium's tables.

**Adding without editing others' rows.** A feature adds its own rows, in its
own file (`rac_actions_<group>.cc`), joined by `All()`. Rows use designated
initializers, so a change to another team's row is one named field on one
line. Each owner above may touch only its own fields on a row it did not
write. A new column needs a default that means "off", so no existing row
changes.

## Tests

- Every row has a risk class and all four hints set (no uninitialized field).
- Ids are unique and match a committed list. Removing an id fails the test.
- `tools/list` for today's 15 tools matches golden bytes.
- No `ai_only` row survives `ForSurface` with AI off, and no outside row
  exists for a "Never" action.
- Default shortcuts don't collide with each other, or with Chromium's and
  Helium's, unless a row says it replaces one.
