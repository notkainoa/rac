#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""The agent's confirm card has no default answer.

A card asks before a step that could send something, change an account, or
carry what the agent read to another site. Nothing on it may be answered by
reflex: its choices look alike, nothing on it takes focus as it appears, and
no key answers it but Esc (stop). Only the plan card has a shortcut, ⌘Return.

rac's WebUI TypeScript has no test target of its own; Chromium's WebUI tests
run in `browser_tests`, which a feature tree can't afford to build. So this
reads agent_cards.ts and app.ts as rac's patches leave them
(patched_files.py) and checks the code that decides each of those.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_agent_confirm_card.py' -v
"""

import re
import unittest

import patched_files

CARDS = 'chrome/browser/resources/rac_ai/agent_cards.ts'
APP = 'chrome/browser/resources/rac_ai/app.ts'
# The answers that let a step run. 'stop' and 'skip' don't.
YES = ('confirm', 'grant', 'always', 'allow', 'allow_once')


def decisions(text):
    """The literal decisions `text` answers a card with."""
    found = []
    for name in ('respond', 'respondToAgent'):
        for args in patched_files.call_args(text, name):
            if len(args) == 2:
                found.append(args[1].strip('\'"'))
    return found


def key_handlers(text):
    """Every key listener's body in `text`."""
    bodies = []
    for match in re.finditer(r"addEventListener\(\s*'key(?:down|up|press)'",
                             text):
        bodies.append(patched_files.braced_body(text[match.start():],
                                                match.group(0)))
    return bodies


class ConfirmCardTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cards = patched_files.final_text(CARDS)
        cls.app = patched_files.final_text(APP)
        cls.card = patched_files.braced_body(cls.cards,
                                             'function buildConfirmCard(')

    def choices(self):
        """The card's makeButton calls, by the string each label names."""
        out = {}
        for args in patched_files.call_args(self.card, 'makeButton'):
            names = re.findall(r"'(\w+)'", args[0])
            self.assertTrue(names, f'a button with no label string: {args}')
            out.setdefault(names[0], []).append(args)
        return out

    def test_the_three_choices_share_one_style(self):
        self.assertIn("kind: 'primary'|'secondary'|'quiet' = 'secondary'",
                      self.cards,
                      'makeButton no longer defaults to the plain style')
        choices = self.choices()
        for label in ('allowOnce', 'flowGrant', 'dontAllowStep'):
            self.assertIn(label, choices, f'the card has no {label} button')
        # Allow and Allow once are one button, labeled by the card.
        self.assertIn("str(confirm.flow ? 'allowOnce' : 'allowStep')",
                      self.card)
        for label in ('allowOnce', 'flowGrant', 'dontAllowStep'):
            for args in choices[label]:
                self.assertEqual(
                    len(args), 2,
                    f'{label} is given a style of its own: {args[2:]}')
        self.assertNotIn("'primary'", self.card,
                         'something on the confirm card is primary')
        self.assertNotIn('primary', re.sub(r'//.*', '', self.card))

    def test_nothing_on_a_card_takes_focus_as_it_appears(self):
        code = re.sub(r'//.*', '', self.card)
        self.assertEqual(len(re.findall(r'\.focus\(', code)),
                         len(re.findall(r'(?<![\w.])card\.focus\(', code)),
                         'something on the card other than the card itself '
                         'takes focus')
        self.assertNotIn('autofocus', code)
        # The card itself only when the user isn't typing, after it draws.
        self.assertIn('if (ctx.mayTakeFocus())', code)
        for text in (self.cards, self.app):
            self.assertIsNone(
                re.search(r'(pill-action|agent-actions|confirm-card)[^;\n]*'
                          r'\.focus\(', text),
                'a card button is focused by selector')

    def test_return_never_answers_a_card(self):
        handlers = key_handlers(self.app) + key_handlers(self.cards)
        self.assertGreaterEqual(len(handlers), 3, 'the key listeners moved')
        for body in handlers:
            for decision in decisions(body):
                if decision == 'stop':
                    continue
                self.assertEqual(decision, 'allow',
                                 f'a key answers a card with {decision!r}')
                # The plan card's shortcut needs ⌘ and the plan card.
                self.assertIn("event.key === 'Enter' && event.metaKey", body)
                self.assertIn("kind === 'plan'", body)
        # The answers that let a step run come from the card's buttons only.
        for decision in decisions(self.app):
            self.assertIn(decision, ('stop', 'allow'),
                          f'app.ts answers a card with {decision!r}')
        for args in patched_files.call_args(self.card, 'respond'):
            decision = args[1].strip('\'"')
            self.assertIn(decision, YES + ('skip', 'stop'))
        button_answers = [
            d for args in patched_files.call_args(self.card, 'makeButton')
            for d in decisions(args[1])
        ]
        self.assertCountEqual(button_answers, decisions(self.card),
                              'the card answers outside a button click')

    def test_command_return_answers_only_the_plan_card(self):
        shortcuts = [
            body for body in key_handlers(self.app)
            if 'metaKey' in body and "'Enter'" in body and
            decisions(body)
        ]
        self.assertEqual(len(shortcuts), 1, 'one ⌘Return shortcut, for plans')
        body = shortcuts[0]
        self.assertEqual(decisions(body), ['allow'])
        # pendingCardId says 'confirm' for a confirm card, risky, data-flow,
        # or any other, so the shortcut's test leaves every one of them out.
        self.assertIn("plan?.kind === 'plan'", body)
        self.assertIn("{kind: 'plan'|'confirm', id: string}|null", self.app)


if __name__ == '__main__':
    unittest.main()
