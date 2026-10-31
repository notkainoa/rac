#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""A never site's text stays out of the chat and the link summary.

The checks themselves (NeverReadHost, PagePromptCache::DropNeverSites) have
unit tests in rac_ai_unittests. The calls to them sit in the chat panel's
page handler and the link summary's controller, which need a browser
window, a WebUI, and a profile, so only `browser_tests` could run them. A
refresh that drops one of those calls leaves everything building and every
unit test green while the rule stops holding. So this reads the two files
as rac's patches leave them (patched_files.py) and checks each call is still
there, in the function that owns it, ahead of what it guards.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_never_site_wiring.py' -v
"""

import re
import unittest

import patched_files

HANDLER = 'chrome/browser/ui/webui/rac_ai/rac_ai_page_handler.cc'
LINKS = 'chrome/browser/ui/views/rac/ai/link_summary_controller.cc'


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
        body = self.function(self.handler, 'void PageHandler::StartSession(')
        drop = 'page_context_.DropNeverSites(SiteRules(profile_))'
        why = ('a rule added mid-conversation must empty the cache before '
               'the next request, for direct providers and agents alike')
        self.assert_before(body, drop, 'StartAgentSession(', why)
        self.assert_before(body, drop, 'session_->Start()', why)
        self.assert_before(body, drop, 'FireWebUIListener("rac-ai-attach-failed"',
                           'the user is no longer told which sites were left out')

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


if __name__ == '__main__':
    unittest.main()
