// Run against a fresh local Mercury process serving markdown-security.ipynb
// with --keep-session=True. Requires the Playwright Node package and Chromium.
// MERCURY_TEST_URL overrides the URL; CHROME_PATH selects a Chrome executable.
// EXPECT_XSS=1 is only for confirming the regression against unpatched source.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {})
  });
  const pages = [];
  const dialogs = [[], [], []];
  const expected = process.env.EXPECT_XSS === '1';
  try {
    async function viewer(index) {
      const context = await browser.newContext();
      const page = await context.newPage();
      page.on('dialog', async dialog => {
        dialogs[index].push(dialog.message());
        await dialog.dismiss();
      });
      await page.goto(process.env.MERCURY_TEST_URL || 'http://127.0.0.1:18765/mercury/markdown-security.ipynb', { waitUntil: 'domcontentloaded' });
      await page.getByPlaceholder('Security test input', { exact: true }).waitFor({ timeout: 60000 });
      pages.push(page);
      return page;
    }
    const a = await viewer(0);
    const b = await viewer(1);
    async function submit(value, marker) {
      const input = a.getByPlaceholder('Security test input', { exact: true });
      await input.fill(value);
      await input.press('Enter');
      await b.getByText(marker, { exact: true }).first().waitFor({ timeout: 30000 });
      await b.waitForTimeout(1500);
    }
    await submit('**BENIGN-CONTROL**', 'BENIGN-CONTROL');
    assert.deepEqual(dialogs, [[], [], []], 'benign control must not execute');
    assert.ok(await b.locator('strong').filter({ hasText: 'BENIGN-CONTROL' }).count());
    await submit('<div>CHAT-CHECK<img src=x onerror="alert(\'CHAT-XSS\')"></div>', 'CHAT-CHECK');
    await submit('STREAM:<div>STREAM-CHECK<img src=x onSPLITerror="alert(\'STREAM-XSS\')"></div>', 'STREAM-CHECK');
    await submit('<div>SCRIPT-CHECK<script>alert("SCRIPT-XSS")</script></div>', 'SCRIPT-CHECK');
    await submit('MD:<div>MD-CHECK<img src=x onerror="alert(\'MD-XSS\')"></div>', 'MD-CHECK');
    const c = await viewer(2);
    await c.getByText('MD-CHECK', { exact: true }).first().waitFor({ timeout: 30000 });
    await c.getByText('STREAM-CHECK', { exact: true }).first().waitFor({ timeout: 30000 });
    await c.waitForTimeout(1500);
    const pids = await Promise.all(pages.map(async page => {
      const text = await page.locator('body').innerText();
      const match = text.match(/KERNEL_PID (\d+)/);
      assert.ok(match, 'kernel identity must be displayed');
      return match[1];
    }));
    assert.equal(new Set(pids).size, 1, 'all viewers must share a kernel');
    if (expected) {
      for (const index of [0, 1, 2]) {
        for (const marker of ['CHAT-XSS', 'STREAM-XSS', 'MD-XSS']) {
          assert.ok(dialogs[index].includes(marker), `viewer ${index} did not execute ${marker}`);
        }
      }
      assert.ok(dialogs[1].includes('SCRIPT-XSS'));
    } else {
      assert.deepEqual(dialogs, [[], [], []], 'sanitized content must not execute');
      for (const page of pages) {
        assert.equal(await page.locator('.mljar-chat-msg-bubble script, .mljar-chat-msg-bubble [onerror]').count(), 0);
      }
    }
    console.log(JSON.stringify({ expectedXss: expected, kernelPids: pids, dialogs }));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
