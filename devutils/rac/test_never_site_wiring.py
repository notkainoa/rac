#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""A never site's text stays out of the chat and the link summary.

The checks themselves (NeverReadHost, PagePromptCache::DropNeverSites,
PrepareCacheForSend) have unit tests in rac_ai_unittests. The calls to them
sit in the chat panel's page handler and the link summary's controller,
which need a browser window, a WebUI, and a profile, so only `browser_tests`
could run them. A
refresh that drops one of those calls leaves everything building and every
unit test green while the rule stops holding. So this reads the two files
as rac's patches leave them (patched_files.py) and checks each call is still
there, in the function that owns it, ahead of what it guards.

AskRowWiringTest pins the same kind of wiring for internal pages and the
command bar's Ask row: the row is offered and run only by AskAssistant()'s
own check, and that check still refuses an internal page.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_never_site_wiring.py' -v
"""

import re
import unittest

import patched_files

HANDLER = 'chrome/browser/ui/webui/rac_ai/rac_ai_page_handler.cc'
LINKS = 'chrome/browser/ui/views/rac/ai/link_summary_controller.cc'
SEND = 'chrome/browser/rac/ai/chat_send.cc'


def code(body):
    """`body` without its comments."""
    return re.sub(r'//.*', '', body)


class NeverSiteWiringTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.handler = patched_files.final_text(HANDLER)
        cls.links = patched_files.final_text(LINKS)

    def function(self, text, opening):
        return code(patched_files.braced_body(text, opening))

    def assert_before(self, body, first, then, why):
        self.assertIn(first, body, why)
        self.assertIn(then, body, f'{then!r} is gone')
        self.assertLess(body.index(first), body.index(then), why)

    def test_the_rules_come_from_the_site_rules_pref(self):
        body = self.function(self.handler, 'SiteRules(Profile* profile) {')
        self.assertIn('rac::agent::ParseSiteRules(', body)
        self.assertIn('GetDict(kAgentSiteRules)', body)

    def test_the_tab_chip_names_a_never_site(self):
        # DescribeTab feeds the current-tab chip and the tab picker; the page
        # shows a tab with "never" as one it can't attach.
        body = self.function(self.handler, 'PageHandler::DescribeTab(')
        self.assertRegex(
            body, r'NeverReadHost\(SiteRules\(profile_\),\s*'
            r'\{\.url = url\.spec\(\)\}\)')
        self.assertIn('dict.Set("never", never);', body)
        app = patched_files.final_text(
            'chrome/browser/resources/rac_ai/app.ts')
        self.assertIn('never?: string;', app)
        self.assertIn('tabs.filter(tab => !tab.never)', app,
                      'the picker no longer leaves never tabs out')
        self.assertIn('attachedTabs().filter(tab => !tab.never)', app,
                      'a send no longer leaves never tabs out')

    def test_the_chat_cache_drops_never_sites_before_each_send(self):
        # Each tab's conversation keeps its own cache (PageHandler::Chat's
        # page_context). StartSession is the one place a request is built,
        # for direct providers and agents alike, and it drops first.
        body = self.function(self.handler, 'void PageHandler::StartSession(')
        drop = 'PrepareCacheForSend(chat.page_context, SiteRules(profile_))'
        why = ('a rule added mid-conversation must empty the cache before '
               'the next request, for direct providers and agents alike')
        self.assert_before(body, drop, 'StartAgentSession(chat,', why)
        self.assert_before(body, drop, 'chat.session->Start()', why)
        self.assert_before(body, drop, 'Emit(chat, kAttachFailedEvent',
                           'the user is no longer told which sites were left out')
        # The seam is the drop itself.
        seam = self.function(patched_files.final_text(SEND),
                             'std::vector<std::string> PrepareCacheForSend(')
        self.assertIn('cache.DropNeverSites(rules)', seam,
                      'the send seam no longer drops never sites')

    def test_every_send_goes_through_the_drop(self):
        handler = code(self.handler)
        # The page's one way to send, HandleSend, reads the attached tabs and
        # then starts the session; nothing else starts one.
        self.assertEqual(handler.count('"racAiSend"'), 1)
        self.assertIn('ReadNextPage(*chat, std::move(send))',
                      self.function(self.handler, 'void PageHandler::HandleSend('))
        self.assertIn('ReadNextPage(chat, std::move(send))',
                      self.function(self.handler, 'void PageHandler::OnPageRead('))
        self.assertEqual(handler.count('StartSession(chat,'), 1,
                         'a request is started outside the one send path')
        self.assertIn('StartSession(chat, std::move(send))',
                      self.function(self.handler, 'void PageHandler::ReadNextPage('))
        # The agent's prompt is built only from StartSession, after the drop.
        self.assertEqual(handler.count('StartAgentSession(chat,'), 1)
        self.assertEqual(handler.count('page_context.Apply('), 1)
        self.assertIn('chat.page_context.Apply(',
                      self.function(self.handler,
                                    'void PageHandler::StartAgentSession('))
        # A direct provider's session gets the cache only in StartSession.
        self.assertEqual(handler.count('&chat.page_context'), 1)
        self.assertIn('&chat.page_context', self.function(
            self.handler, 'void PageHandler::StartSession('))
        # Every way the page sends (the composer, Ask, retry, the new tab
        # page's question) ends in the one racAiSend, in startReply.
        app = code(patched_files.final_text(
            'chrome/browser/resources/rac_ai/app.ts'))
        self.assertEqual(app.count("'racAiSend'"), 1)
        self.assertIn("'racAiSend'", code(patched_files.braced_body(
            app, 'function startReply(question: Message) {')))

    def test_attached_tabs_on_never_sites_are_not_read(self):
        body = self.function(self.handler, 'void PageHandler::ReadNextPage(')
        self.assert_before(body, 'NeverReadHost(SiteRules(profile_), {.url = url})',
                           'ExtractPageText(',
                           'a never tab is read before the rule is checked')
        body = self.function(self.handler, 'void PageHandler::OnPageRead(')
        self.assert_before(body, 'NeverReadHost(SiteRules(profile_), *result)',
                           'send->pages.push_back(',
                           'a page with a never frame reaches the prompt')

    def test_the_link_summary_refuses_never_sites(self):
        refuse = self.function(self.links,
                               'bool RefuseNeverSite(const PageText& page) {')
        self.assertIn('NeverReadHost(', refuse)
        self.assertIn('GetDict(kAgentSiteRules)', refuse)
        self.assertIn('IDS_RAC_AI_NEVER_SITE', refuse)
        start = self.function(self.links, 'bool Start(const gfx::Point& pointer) {')
        self.assert_before(start, 'if (RefuseNeverSite(link)) {',
                           'CacheFor(profile_).Get(link_)',
                           'a cached summary of a never site still shows')
        self.assert_before(start, 'if (RefuseNeverSite(link)) {',
                           'std::make_unique<LinkFetcher>(',
                           'a never link is fetched')
        fetched = self.function(
            self.links, 'void OnFetched(LinkFetcher::Result result) {')
        self.assert_before(fetched, 'if (RefuseNeverSite(*result)) {',
                           'BuildLinkSummaryRequest(',
                           'a redirect or frame to a never site is summarized')


class AskRowWiringTest(unittest.TestCase):
    ROWS = 'chrome/browser/rac/actions/rac_actions_command_bar.cc'
    TABLE = 'chrome/browser/rac/actions/rac_actions.cc'
    CONTEXT = 'chrome/browser/ui/rac/rac_action_handlers.cc'
    BAR = 'chrome/browser/ui/views/rac/command_bar/command_bar_actions.cc'
    PANEL = 'chrome/browser/ui/views/rac/ai/assistant_side_panel.cc'

    def function(self, path, opening):
        return code(patched_files.braced_body(
            patched_files.final_text(path), opening))

    assert_before = NeverSiteWiringTest.assert_before

    def test_the_ask_row_needs_the_assistant_not_a_web_page(self):
        rows = code(patched_files.final_text(self.ROWS))
        start = rows.index('.id = "ask",')
        row = rows[start:rows.index('.hints', start)]
        self.assertIn('Need::kAssistant', row)
        self.assertNotIn('Need::kWebPage', row,
                         'view-source: shows the row again: its committed '
                         'page is http(s)')
        self.assertIn('context.can_ask_assistant',
                      self.function(self.TABLE, 'bool MeetsNeeds('))

    def test_the_need_is_ask_assistants_own_check(self):
        body = self.function(self.CONTEXT,
                             'ActionContext ContextForWindow(')
        self.assertRegex(
            body, r'if \(context\.ai_enabled && !context\.incognito\) \{\s*'
            r'context\.can_ask_assistant = rac::ai::CanAskAssistant\(browser\);',
            'the Ask row no longer goes by AskAssistant()\'s check, or runs '
            'AI code with AI off')

    def test_ask_assistant_still_refuses_internal_pages(self):
        can = self.function(self.PANEL, 'bool CanAskAssistant(')
        self.assertIn('IsAssistantBlockedHere(browser)', can)
        ask = self.function(self.PANEL, 'bool AskAssistant(')
        self.assert_before(ask, '!CanAskAssistant(browser)',
                           'ShowAssistantForTab(',
                           'the panel opens before the internal-page check')
        self.assert_before(ask, '!CanAskAssistant(browser)', 'SetPrompt(',
                           'the prompt is left before the internal-page check')

    def test_the_bar_checks_again_before_it_runs_a_row(self):
        body = self.function(self.BAR, 'bool RunAction(')
        self.assert_before(body, 'ContextForWindow(browser)',
                           'RunBrowserAction(',
                           'a row runs without its availability checked again')
        self.assert_before(body, 'ForSurface(Surface::kCommandBar, context)',
                           'RunBrowserAction(',
                           'a row runs without its availability checked again')


if __name__ == '__main__':
    unittest.main()
