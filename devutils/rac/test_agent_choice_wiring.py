#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Choosing an agent from the chat goes through the browser's checks.

The checks themselves (OfferedAgentIds, AgentsInShownMenu, AgentForPick,
ChooseOfferedAgent) have unit tests in rac_ai_unittests. The calls to them
sit in the chat's page handler, which needs a browser window, a WebUI, and a
profile, so only `browser_tests` could run them. A refresh that drops one of
those calls leaves everything building and every unit test green while the
page can make any agent active, installed or not. So this reads the handler
and the page as rac's patches leave them (patched_files.py) and checks each
step is still there, in the function that owns it.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_agent_choice_wiring.py' -v
"""

import re
import unittest

import patched_files

HANDLER = 'chrome/browser/ui/webui/rac_ai/rac_ai_page_handler.cc'
APP = 'chrome/browser/resources/rac_ai/app.ts'


def code(body):
    """`body` without its comments or blank space runs."""
    return re.sub(r'\s+', ' ', re.sub(r'//.*', '', body))


class AgentChoiceWiringTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.handler = patched_files.final_text(HANDLER)
        cls.app = patched_files.final_text(APP)

    def function(self, opening):
        return code(patched_files.braced_body(self.handler, opening))

    def test_the_choice_goes_through_choose_offered_agent(self):
        body = self.function('void PageHandler::HandleSelectAgent(')
        self.assertIn('std::exchange(picked_agent_, std::string())', body,
                      'a pick must be used once and then forgotten')
        self.assertRegex(
            body, r'ChooseOfferedAgent\(profile_->GetPrefs\(\), picked, \*id\)',
            'the handler must check the picked agent before choosing')
        # The only way to write the pref is through the check.
        inside = body[body.index('{'):]
        self.assertNotIn('SelectAgent(',
                         inside.replace('ChooseOfferedAgent(', ''))
        self.assertNotIn('SetString(', inside)
        self.assertIn('ResolveJavascriptCallback(args[0], base::Value(chosen))',
                      body, 'the page must hear whether the browser took it')

    def test_the_menu_offers_only_what_it_built(self):
        body = self.function('void PageHandler::ResolveModelMenu(')
        self.assertIn('offered_agents_ = OfferedAgentIds(menu);', body)

    def test_only_agents_with_a_line_in_the_open_menu_can_be_picked(self):
        body = self.function('void PageHandler::HandleShowMenu(')
        self.assertIn('menu_agents_ = AgentsInShownMenu(lines, offered_agents_);',
                      body)
        self.assertIn('offered_agents_.clear();', body)
        self.assertLess(body.index('AgentsInShownMenu('),
                        body.index('offered_agents_.clear();'))

    def test_a_pick_names_the_agent(self):
        body = self.function('void PageHandler::OnMenuPicked(')
        self.assertIn('picked_agent_ = AgentForPick(id, menu_agents_);', body)

    def test_closing_the_menu_ends_its_choices(self):
        for opening in ('void PageHandler::OnMenuClosed(',
                        'void PageHandler::CloseMenu() {'):
            self.assertIn('menu_agents_.clear();', self.function(opening),
                          opening)

    def test_bad_page_input_never_crashes_the_browser(self):
        for opening in ('void PageHandler::HandleSelectAgent(',
                        'void PageHandler::HandleGetModelMenu(',
                        'void PageHandler::HandleShowMenu('):
            body = self.function(opening)
            self.assertNotIn('CHECK', body, opening)
            self.assertRegex(body, r'if \(args\.size\(\) != \d\) \{ return; \}',
                             opening)

    def test_the_page_shows_an_agent_only_once_the_browser_took_it(self):
        body = code(patched_files.braced_body(
            self.app, 'async function selectAgent('))
        self.assertIn("sendWithPromise<boolean>('racAiSelectAgent', id)", body)
        self.assertNotIn('sendToBrowser(', body)
        answer = body.index("if (!chosen) {")
        for shown in ('noteSwitch(', 'agentId = id', 'showProvider('):
            self.assertLess(answer, body.index(shown), shown)


if __name__ == '__main__':
    unittest.main()
