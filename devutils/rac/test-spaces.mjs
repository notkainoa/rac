// Copyright 2026 The rac Authors
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Focused, real-browser regression test for spaces. Requires Node 22+ and a
// built worktree (source dev.sh && he build). Uses a fresh profile in build/
// and loopback-only pages and debugging, never the dev or daily profile. The
// browser starts with --rac-launch-in-background, so it never takes focus.
// Run from the worktree root, only with permission to automate the browser:
//   node devutils/rac/test-spaces.mjs

import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {mkdtemp, mkdir, writeFile} from 'node:fs/promises';
import {createServer} from 'node:http';
import {createServer as createSocketServer} from 'node:net';
import {dirname, join, resolve} from 'node:path';
import {setTimeout as delay} from 'node:timers/promises';
import {fileURLToPath} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');

async function waitFor(check, description, timeout = 15000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const value = await check();
    if (value) return value;
    await delay(100);
  }
  throw new Error(`Timed out waiting for ${description}`);
}

async function freePort() {
  const server = createSocketServer();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}

async function connect(url) {
  const socket = new WebSocket(url);
  await once(socket, 'open');
  let next = 0;
  const pending = new Map();
  socket.addEventListener('message', ({data}) => {
    const message = JSON.parse(data);
    const request = pending.get(message.id);
    if (!request) return;
    pending.delete(message.id);
    clearTimeout(request.timeout);
    if (message.error) request.reject(new Error(JSON.stringify(message.error)));
    else request.resolve(message.result);
  });
  socket.addEventListener('close', () => {
    for (const request of pending.values()) {
      clearTimeout(request.timeout);
      request.reject(new Error('Browser disconnected'));
    }
    pending.clear();
  });
  return {
    call(method, params = {}, sessionId) {
      return new Promise((resolve, reject) => {
        const id = ++next;
        const timeout = setTimeout(() => {
          pending.delete(id);
          reject(new Error(`Timed out: ${method}`));
        }, 15000);
        pending.set(id, {resolve, reject, timeout});
        socket.send(JSON.stringify({id, method, params, sessionId}));
      });
    },
    close() { socket.close(); },
  };
}

function attributes(node) {
  const result = {};
  for (let i = 0; i < (node.attributes || []).length; i += 2) {
    result[node.attributes[i]] = node.attributes[i + 1];
  }
  return result;
}

function flatten(node) {
  return [node, ...(node.children || []).flatMap(flatten)];
}

function isClass(name) {
  return node => attributes(node).class === name;
}

async function click(ui, node) {
  assert.ok(node, 'native control exists');
  for (const type of ['mousePressed', 'mouseReleased']) {
    await ui.call('DOM.dispatchMouseEvent', {
      nodeId: node.nodeId,
      event: {type, x: 12, y: 12, button: 'left', wheelDirection: 'none'},
    });
  }
}

async function run() {
  const profile = await mkdtemp(join(root, 'build/spaces-test-'));
  await mkdir(join(profile, 'Default'));
  await writeFile(join(profile, 'Default/Preferences'), JSON.stringify({
    helium: {browser: {layout: 2}},
  }));
  const uiPort = await freePort();
  const cdpPort = await freePort();
  const server = createServer((request, response) => {
    const name = request.url === '/a' ? 'Space A' : 'Space B';
    response.setHeader('Content-Type', 'text/html');
    response.end(`<title>${name}</title><h1>${name}</h1><input id="draft">
      <script>window.identity = Math.random()</script>`);
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const origin = `http://127.0.0.1:${server.address().port}`;
  const launchArgs = [
    'run', `--user-data-dir=${profile}`, `--enable-ui-devtools=${uiPort}`,
    `--remote-debugging-port=${cdpPort}`, '--remote-debugging-address=127.0.0.1',
    '--enable-features=ui-debug-tools-enable-synthetic-events',
    '--rac-launch-in-background',
    '--no-first-run', '--no-default-browser-check',
    '--disable-background-networking', '--disable-component-update',
  ];
  let logs = '';
  let browser;
  const launch = () => {
    browser = spawn(join(root, 'devutils/rac/worktree.sh'), launchArgs,
                    {cwd: root, stdio: ['ignore', 'pipe', 'pipe']});
    browser.stdout.on('data', chunk => { logs += chunk; });
    browser.stderr.on('data', chunk => { logs += chunk; });
  };
  let cdp;
  let ui;
  const attach = async () => {
    const endpoint = await waitFor(async () => {
      if (browser.exitCode !== null || browser.signalCode) {
        throw new Error('Browser exited during startup');
      }
      try {
        return await (await fetch(
            `http://127.0.0.1:${cdpPort}/json/version`)).json();
      } catch { return null; }
    }, 'browser debugging endpoint', 120000);
    cdp = await connect(endpoint.webSocketDebuggerUrl);
    ui = await connect(`ws://127.0.0.1:${uiPort}/0`);
  };
  try {
    launch();
    await attach();
    const tree = async () => flatten((await ui.call('DOM.getDocument')).root);
    await waitFor(async () => (await tree()).some(isClass('SpaceDotButton')),
                  'initial space');

    const {targetId: first} = await cdp.call('Target.createTarget',
                                            {url: `${origin}/a`});
    const {sessionId} = await cdp.call('Target.attachToTarget',
                                      {targetId: first, flatten: true});
    const evaluate = async expression => {
      const result = await cdp.call('Runtime.evaluate',
                                    {expression, returnByValue: true},
                                    sessionId);
      assert.ok(!result.exceptionDetails, 'page evaluation succeeded');
      return result.result.value;
    };
    // Clicks the space's dot until the first page reaches `state`. The dots
    // are rebuilt when spaces change, so a click on a stale node is lost and
    // is tried again.
    const showSpace = async (index, state, description) => {
      for (let attempt = 0; attempt < 3; ++attempt) {
        await click(ui, (await tree()).filter(isClass('SpaceDotButton'))[index]);
        try {
          return await waitFor(
              () => evaluate(`document.visibilityState === "${state}"`),
              description, 3000);
        } catch (error) {
          if (attempt === 2) throw error;
        }
      }
    };
    await waitFor(() => evaluate('document.title === "Space A"'), 'test page');
    await cdp.call('Target.activateTarget', {targetId: first});
    await waitFor(() => evaluate('document.visibilityState === "visible"'),
                  'first page to be active before switching');
    const identity = await evaluate('window.identity');
    await evaluate('document.querySelector("#draft").value = "keep this draft"');
    const windowBefore = await cdp.call('Browser.getWindowForTarget',
                                        {targetId: first});

    const switcher = (await tree()).find(isClass('SpaceSwitcherView'));
    await click(ui, switcher.children.find(isClass('LabelButton')));
    await waitFor(async () =>
      (await tree()).filter(isClass('SpaceDotButton')).length === 2,
      'second space');

    // Tabs of a hidden space stay in the window's tab strip, so the hidden
    // page must still belong to a real browser window.
    const windowHidden = await cdp.call('Browser.getWindowForTarget',
                                        {targetId: first}).catch(error => ({error}));
    await waitFor(() => evaluate('document.visibilityState === "hidden"'),
                  'first space content to be hidden');

    // Give delayed work on the hidden page time to run (the first space's
    // hidden tabs are only unloaded after 15 minutes, which this doesn't wait
    // for), and check the browser is still up.
    await delay(2000);
    assert.equal(browser.exitCode, null, 'browser survived the hidden space');
    assert.equal(browser.signalCode, null, 'browser did not crash');
    assert.ok(!windowHidden.error, 'hidden tab still has a real browser window');
    assert.equal(windowHidden.windowId, windowBefore.windowId);
    assert.equal(await evaluate('window.identity'), identity);
    assert.equal(await evaluate('document.querySelector("#draft").value'),
                 'keep this draft');

    const firstDot = (await tree()).filter(isClass('SpaceDotButton'))[0];
    await click(ui, firstDot);
    await waitFor(() => evaluate('document.visibilityState === "visible"'),
                  'first space to be shown again');
    assert.equal(await evaluate('window.identity'), identity,
                 'warm switching must not reload the page');
    console.log('PASS: ownership, hidden state, warm state');

    for (const type of ['rawKeyDown', 'keyUp']) {
      await cdp.call('Input.dispatchKeyEvent', {
        type, key: '2', code: 'Digit2', windowsVirtualKeyCode: 50,
        nativeVirtualKeyCode: 19, modifiers: 2,
      }, sessionId);
    }
    await waitFor(() => evaluate('document.visibilityState === "hidden"'),
                  'keyboard space switch');
    const {targetId: second} = await cdp.call('Target.createTarget',
                                             {url: `${origin}/b`});
    const {sessionId: secondSession} = await cdp.call('Target.attachToTarget',
                                       {targetId: second, flatten: true});
    const evaluateSecond = async expression => (await cdp.call(
      'Runtime.evaluate', {expression, returnByValue: true}, secondSession)).result.value;
    await waitFor(() => evaluateSecond('document.title === "Space B"'),
                  'second page');
    await cdp.call('Target.activateTarget', {targetId: second});
    const sessions = new Map([[first, sessionId], [second, secondSession]]);
    const pageKey = async (key, code, virtualKey, modifiers) => {
      let activeSession;
      for (const target of (await cdp.call('Target.getTargets')).targetInfos) {
        if (target.type !== 'page') continue;
        if (!sessions.has(target.targetId)) {
          sessions.set(target.targetId, (await cdp.call('Target.attachToTarget',
            {targetId: target.targetId, flatten: true})).sessionId);
        }
        const candidate = sessions.get(target.targetId);
        const visible = await cdp.call('Runtime.evaluate',
          {expression: 'document.visibilityState === "visible"',
           returnByValue: true}, candidate);
        if (visible.result.value) { activeSession = candidate; break; }
      }
      assert.ok(activeSession, 'active page receives keyboard events');
      for (const type of ['rawKeyDown', 'keyUp']) {
        await cdp.call('Input.dispatchKeyEvent', {
          type, key, code, windowsVirtualKeyCode: virtualKey, modifiers,
          nativeVirtualKeyCode: {'1': 18, '2': 19, '9': 25, Tab: 48, ArrowLeft: 123,
                                 ArrowRight: 124}[key],
        }, activeSession);
      }
    };
    await pageKey('1', 'Digit1', 49, 4); // Cmd+1, first tab in this space.
    await waitFor(() => evaluateSecond('document.visibilityState === "hidden"'),
                  'first visible tab shortcut');
    assert.equal(await evaluate('document.visibilityState'), 'hidden');
    await pageKey('9', 'Digit9', 57, 4); // Cmd+9, last tab in this space.
    await waitFor(() => evaluateSecond('document.visibilityState === "visible"'),
                  'last visible tab shortcut');
    let drawnTabs = 0;
    for (const node of await tree()) {
      if (!['Tab', 'TabView', 'VerticalTabView', 'HorizontalTabView']
          .includes(attributes(node).class)) continue;
      const styles = await ui.call('CSS.getMatchedStylesForNode',
                                   {nodeId: node.nodeId});
      const properties = Object.fromEntries(styles.matchedCSSRules.flatMap(
        match => match.rule.style.cssProperties.map(p => [p.name, p.value])));
      if (properties.IsDrawn === 'true' && Number(properties.Height) > 0 &&
          Number(properties.Width) > 0) ++drawnTabs;
    }
    assert.equal(drawnTabs, 2, 'native tab strip only draws this space’s tabs');
    for (let i = 0; i < 4; ++i) {
      await pageKey('Tab', 'Tab', 9, 2); // Ctrl+Tab.
      assert.equal(await evaluate('document.visibilityState'), 'hidden',
                   'tab cycling cannot select another space');
    }
    console.log('PASS: space shortcuts and visible-only tab navigation');

    // Ctrl+Left and Ctrl+Right move to the previous and next space, Ctrl+1
    // shows the first. The second space is showing, so the first page is
    // hidden.
    await pageKey('ArrowLeft', 'ArrowLeft', 37, 2);
    await waitFor(() => evaluate('document.visibilityState === "visible"'),
                  'previous space shortcut');
    await pageKey('ArrowRight', 'ArrowRight', 39, 2);
    await waitFor(() => evaluate('document.visibilityState === "hidden"'),
                  'next space shortcut');
    await pageKey('1', 'Digit1', 49, 2);
    await waitFor(() => evaluate('document.visibilityState === "visible"'),
                  'first space shortcut');
    await pageKey('2', 'Digit2', 50, 2);
    await waitFor(() => evaluate('document.visibilityState === "hidden"'),
                  'second space shortcut');
    console.log('PASS: next, previous, and numbered space shortcuts');

    const timings = [];
    for (let i = 0; i < 12; ++i) {
      const start = performance.now();
      await showSpace(i % 2, i % 2 ? 'hidden' : 'visible', 'warm space switch');
      timings.push(performance.now() - start);
    }
    timings.sort((a, b) => a - b);
    console.log(`Warm native switch median: ${timings[6].toFixed(1)} ms ` +
                `(includes debugging round trips, not a Helium comparison)`);

    await click(ui, (await tree()).filter(isClass('SpaceDotButton'))[0]);
    await waitFor(() => evaluate('document.visibilityState === "visible"'),
                  'first space before new window');
    const secondIdentity = await evaluateSecond('window.identity');
    await cdp.call('Target.createTarget', {url: 'about:blank', newWindow: true});
    await waitFor(async () => (await cdp.call('Browser.getWindowForTarget',
      {targetId: second})).windowId !== windowBefore.windowId,
      'free space to move into the new real window');
    assert.equal(await evaluateSecond('window.identity'), secondIdentity);
    await waitFor(() => evaluateSecond('document.visibilityState === "visible"'),
                  'new window to show its space');
    // Close the window, not its individual tabs: this must snapshot all spaces
    // it owns before Chromium destroys their contents.
    await cdp.call('Input.dispatchKeyEvent', {
      type: 'rawKeyDown', key: 'w', code: 'KeyW',
      windowsVirtualKeyCode: 87, nativeVirtualKeyCode: 13, modifiers: 12,
    }, secondSession).catch(() => {});
    await waitFor(async () => !(await cdp.call('Target.getTargets')).targetInfos
      .some(target => target.targetId === second), 'second window to close');
    assert.equal(await evaluate('window.identity'), identity);
    await click(ui, (await tree()).filter(isClass('SpaceDotButton'))[1]);
    const restoredSecond = await waitFor(async () =>
      (await cdp.call('Target.getTargets')).targetInfos.find(
        target => target.url === `${origin}/b`), 'closed space to restore');
    assert.notEqual(restoredSecond.targetId, second);
    console.log('PASS: real-window transfer and closed-window restoration');

    await cdp.call('Browser.close').catch(() => {});
    cdp.close();
    ui.close();
    await waitFor(() => browser.exitCode !== null || browser.signalCode,
                  'clean browser exit');
    launch();
    await attach();
    const restored = await waitFor(async () => {
      const pages = (await cdp.call('Target.getTargets')).targetInfos;
      return pages.some(t => t.url === `${origin}/a`) &&
             pages.some(t => t.url === `${origin}/b`) ? pages : null;
    }, 'both spaces after restarting the same isolated profile');
    for (const name of ['a', 'b']) {
      const matches = restored.filter(t => t.url === `${origin}/${name}`);
      assert.equal(matches.length, 1, 'session restore must not duplicate tabs');
      const {sessionId: restoredSession} = await cdp.call('Target.attachToTarget',
        {targetId: matches[0].targetId, flatten: true});
      await click(ui, (await tree()).filter(isClass('SpaceDotButton'))[
        name === 'a' ? 0 : 1]);
      await waitFor(async () => (await cdp.call('Runtime.evaluate',
        {expression: 'document.visibilityState === "visible"',
         returnByValue: true}, restoredSession).catch(error => {
           if (/navigated or closed|Cannot find context/.test(error.message)) {
             return {result: {value: false}};
           }
           throw error;
         })).result.value,
        `restored space ${name} to be selectable`);
    }
    console.log('PASS: quit/relaunch preserves space membership without duplicates');
  } finally {
    if (cdp) {
      await cdp.call('Browser.close').catch(() => {});
      cdp.close();
    }
    ui?.close();
    if (browser.exitCode === null && !browser.signalCode) {
      await Promise.race([once(browser, 'exit'), delay(5000)]);
      if (browser.exitCode === null && !browser.signalCode) browser.kill('SIGTERM');
    }
    server.close();
    await writeFile(join(profile, 'test-browser.log'), logs);
    console.log(`Test profile and log: ${profile}`);
  }
}

run().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
