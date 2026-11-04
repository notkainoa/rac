#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""With AI off, the Assistant has no menu item, no shortcut row, and no key.

The View menu's Assistant item, its Option-Command-A key, and its row on
the keyboard shortcuts page come from Helium and Chromium files that rac
hooks (ai/ai-off-entry-points.patch). Checking them for real needs the Mac
main menu, a browser window, and a profile, so only `browser_tests` could.
A refresh that drops one of the hooks leaves everything building and every
unit test green while "Assistant" shows with AI off again. So this reads the
patch's lines for the upstream files, and the rac-owned files as rac's
patches leave them (patched_files.py), and checks each hook is still there.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_ai_off_entry_points.py' -v
"""

from pathlib import Path
import re
import unittest

import patched_files

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / 'patches/rac/ai/ai-off-entry-points.patch'
ACTIONS = 'chrome/browser/ui/views/rac/ai/assistant_actions.cc'
TABLE_SHORTCUTS = 'chrome/browser/rac/power/shortcuts/table_shortcuts.cc'
MENU_ITEMS = 'chrome/browser/ui/rac/rac_action_menu_items.mm'
RAC_ACTIONS = 'chrome/browser/rac/actions/rac_actions.cc'


def code(body):
    """`body` without its comments or blank space runs."""
    return re.sub(r'\s+', ' ', re.sub(r'//.*', '', body))


def hunks_by_file(patch_text):
    """Maps each patched file to its hunks, each as (removed, added) lines."""
    files = {}
    current = None
    for line in patch_text.splitlines():
        if line.startswith('+++ '):
            current = files.setdefault(line[4:].removeprefix('b/'), [])
        elif line.startswith('--- '):
            continue
        elif line.startswith('@@') and current is not None:
            current.append(([], []))
        elif current and line[:1] in '+-':
            current[-1][0 if line[0] == '-' else 1].append(line[1:])
    return files


class AiOffEntryPointsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hunks = hunks_by_file(PATCH.read_text(encoding='utf-8'))
        cls.series = (ROOT / 'patches/series').read_text().splitlines()

    def added(self, path):
        self.assertIn(path, self.hunks, f'the patch no longer edits {path}')
        return code('\n'.join(line for _, added in self.hunks[path]
                              for line in added))

    def removed(self, path):
        return code('\n'.join(line for removed, _ in self.hunks.get(path, [])
                              for line in removed))

    def function(self, path, opening):
        return code(patched_files.braced_body(
            patched_files.final_text(path), opening))

    def test_the_patch_is_last_after_what_it_hooks(self):
        name = 'rac/ai/ai-off-entry-points.patch'
        self.assertIn(name, self.series)
        at = self.series.index(name)
        for earlier in ('rac/ai/06-new-tab-page-and-entry-points.patch',
                        'rac/ai/08-chat-interaction-fixes.patch',
                        'rac/core/action-table.patch',
                        'rac/power/shortcut-hooks.patch',
                        'rac/command-bar/command-bar.patch'):
            self.assertLess(self.series.index(earlier), at, earlier)

    def test_the_command_follows_the_ai_switch(self):
        path = 'chrome/browser/ui/browser_command_controller.cc'
        added = self.added(path)
        self.assertIn('rac::ai::ObserveAssistantCommand(profile_pref_registrar_, '
                      'browser_, command_updater_.get());', added,
                      'no window hears AI turning on or off')
        self.assertIn('rac::ai::UpdateAssistantCommand(browser_, '
                      'command_updater_.get());', added)
        # The old unconditional enable is gone, not left beside the new one.
        self.assertIn('IDC_RAC_ASSISTANT_TOGGLE', self.removed(path))
        self.assertNotIn('UpdateCommandEnabled( IDC_RAC_ASSISTANT_TOGGLE', added)

    def test_the_command_runs_only_with_ai_on(self):
        body = self.function(
            ACTIONS, 'bool CanRunAssistantCommand(BrowserWindowInterface* browser) {')
        self.assertIn('IsAiEnabled(profile->GetPrefs())', body)
        self.assertIn('IsRegularProfile()', body)
        body = self.function(ACTIONS, 'void UpdateAssistantCommand(')
        self.assertIn('UpdateCommandEnabled(IDC_RAC_ASSISTANT_TOGGLE, '
                      'CanRunAssistantCommand(browser));', body)
        body = self.function(ACTIONS, 'void ObserveAssistantCommand(')
        self.assertIn('registrar.Add(kEnabled,', body)
        self.assertIn('&UpdateAssistantCommand', body)

    def test_the_view_menu_hides_the_item_with_ai_off(self):
        added = self.added('chrome/browser/ui/views/frame/browser_native_widget_mac.mm')
        self.assertIn('#include "chrome/browser/ui/views/rac/ai/assistant_actions.h"',
                      added)
        self.assertRegex(
            added, r'case IDC_RAC_ASSISTANT_TOGGLE: \{ '
            r'result->set_hidden_state = true; '
            r'result->new_hidden_state = rac::ai::HidesAssistantMenuItem\(browser\);')
        body = self.function(
            ACTIONS, 'bool HidesAssistantMenuItem(BrowserWindowInterface* browser) {')
        self.assertIn('return !IsAiEnabled(', body)

    def test_the_view_menu_hides_the_item_with_no_window(self):
        added = self.added('chrome/browser/app_controller_mac.mm')
        self.assertIn('if (tag == IDC_RAC_ASSISTANT_TOGGLE) { '
                      '[base::apple::ObjCCast<NSMenuItem>(item) setHidden:YES];',
                      added)

    def test_the_shortcut_page_has_no_assistant_row_with_ai_off(self):
        added = self.added(
            'chrome/browser/ui/browser_shortcuts/browser_shortcut_metadata.cc')
        self.assertIn('if (prefs && !rac::power::IsTableAiOn(prefs)) { '
                      'return std::nullopt; }', added)
        body = self.function(
            TABLE_SHORTCUTS,
            'void ObserveTableShortcutPrefs(PrefChangeRegistrar& registrar,')
        self.assertIn('registrar.Add(rac::ai::kEnabled, callback);', body,
                      'the shortcut page no longer hears AI turning on or off')

    def test_an_ai_only_row_gets_no_menu_item(self):
        body = self.function(MENU_ITEMS, 'void InsertActionMenuItems(NSMenu* main_menu) {')
        # The table walks its rows in a loop or a ForEachAction lambda; a
        # row the main menu must not build is skipped either way.
        self.assertRegex(body, r'if \(!IsBuiltIntoMainMenu\(action\)\) \{ (continue|return); \}',
                         'the menu hook no longer skips ai_only rows')
        body = self.function(RAC_ACTIONS,
                             'bool IsBuiltIntoMainMenu(const Action& action) {')
        self.assertIn('!action.ai_only', body)


if __name__ == '__main__':
    unittest.main()
