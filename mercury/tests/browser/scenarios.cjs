// Run with: node mercury/tests/browser/scenarios.cjs (requires Playwright Chromium).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '../../..');

// Exercise the actual AppModel protocol: one local acknowledged batch, earliest
// input, no response to another viewer's request, no duplicate rerun.
function testExecutionBridge() {
  const source = fs.readFileSync(
    path.join(root, 'packages/lab/src/mercury/app/model.ts'),
    'utf8'
  );
  const exports = {};
  vm.runInNewContext(
    ts.transpileModule(source, {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2020
      }
    }).outputText,
    { exports, require: () => ({}), console }
  );
  const model = Object.create(exports.AppModel.prototype);
  model._context = {
    model: {
      cells: [
        { id: 'setup' },
        { id: 'growth' },
        { id: 'price' },
        { id: 'scenarios' }
      ]
    }
  };
  model._scenarioRequests = new Map();
  model._updateMessages = new Map();
  const updates = [];
  model._widgetUpdated = { emit: value => updates.push(value) };
  function message(direction, event, extras = {}) {
    model._onKernelMessage(null, {
      direction,
      msg: {
        channel: direction === 'send' ? 'shell' : 'iopub',
        header: { msg_type: 'comm_msg', msg_id: 'message' },
        parent_header: {},
        content: {
          comm_id: 'scenarios-widget',
          data: {
            method: 'custom',
            content: {
              event,
              request_id: 'load-1',
              ...extras
            }
          }
        }
      }
    });
  }
  message('recv', 'scenario_loaded', {
    changed: true,
    source_cell_ids: ['price', 'growth']
  });
  assert.equal(updates.length, 0);
  message('send', 'scenario_load');
  message('recv', 'scenario_loaded', {
    changed: true,
    source_cell_ids: ['price', 'growth']
  });
  assert.equal(updates.length, 1);
  assert.equal(updates[0].cellModelId, 'growth');
  message('recv', 'scenario_loaded', {
    changed: true,
    source_cell_ids: ['growth']
  });
  assert.equal(updates.length, 1);
  message('send', 'scenario_load');
  message('recv', 'scenario_loaded', { changed: false, source_cell_ids: [] });
  assert.equal(updates.length, 1);
  message('send', 'scenario_save');
  message('recv', 'scenario_saved');
  assert.equal(updates.length, 1);
}

const html = `<!doctype html><html><head><link rel="stylesheet" href="/widget.css"></head>
<body><main data-scenario-notebook="/app/forecast.ipynb"><input aria-label="Growth" value="5"><div id="widget"></div></main>
<script type="module">
import widget from '/widget.js';
const listeners = new Map();
window.state = { storage_key: 'forecast', ready: true, running: false, error: '' };
window.requests = [];
window.resultValue = 1000;
window.model = {
  get: name => state[name],
  on: (name, callback) => { if (!listeners.has(name)) listeners.set(name, new Set()); listeners.get(name).add(callback); },
  off: (name, callback) => listeners.get(name)?.delete(callback),
  send: content => {
    requests.push(content);
    setTimeout(() => {
      const { request_id } = content;
      if (content.event === 'scenario_save') emit('msg:custom', {
        event: 'scenario_saved', request_id,
        snapshot: { version: 1, name: content.name, saved_at: '2026-09-11',
          inputs: { Growth: Number(document.querySelector('input').value) }, input_types: { Growth: 'NumberInputWidget' },
          outputs: { Revenue: { kind: 'scalar', value: resultValue },
            Forecast: {kind: 'table', columns: ['Month', 'Revenue'], dtypes: ['str', 'int'], rows: Array.from({length: 12}, (_, i) => ['M' + (i+1), 12-i])},
            Plot: {kind: 'plot', mime: 'image/png', data: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6lYQAAAAASUVORK5CYII='}
          }
        }
      });
      else {
        document.querySelector('input').value = content.snapshot.inputs.Growth;
        state.ready = false;
        emit('change:ready');
        emit('msg:custom', {event: 'scenario_loaded', request_id, changed: true, source_cell_ids: ['growth']});
      }
    }, 10);
  }
};
window.emit = (name, value) => listeners.get(name)?.forEach(callback => callback(value));
window.dispose = await widget.render({ model, el: document.querySelector('#widget') });
window.rendered = true;
</script></body></html>`;

(async () => {
  testExecutionBridge();
  const server = http.createServer((req, res) => {
    if (req.url === '/widget.js') {
      res.setHeader('Content-Type', 'text/javascript');
      res.end(fs.readFileSync(path.join(root, 'mercury/_scenarios.js')));
    } else if (req.url === '/widget.css') {
      res.setHeader('Content-Type', 'text/css');
      res.end(fs.readFileSync(path.join(root, 'mercury/_scenarios.css')));
    } else res.end(html);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({
      viewport: { width: 1200, height: 900 }
    });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const url = `http://127.0.0.1:${server.address().port}`;
    await page.goto(url);
    await page.waitForFunction(() => window.rendered);
    // Scenario controls follow the same config.toml theme tokens as Select/Button.
    await page.evaluate(() => {
      document.body.style.setProperty('--mercury-primary-color', '#123456');
      document.body.style.setProperty('--mercury-border-radius', '14px');
      document.body.style.setProperty('--mercury-widget-background-color', '#fafafa');
    });
    await page.waitForFunction(() =>
      getComputedStyle(document.querySelector('.ms-primary-actions .ms-button')).backgroundColor === 'rgb(18, 52, 86)'
    );
    const styles = await page.evaluate(() => {
      const button = getComputedStyle(document.querySelector('.ms-primary-actions .ms-button'));
      const select = getComputedStyle(document.querySelector('.ms-selector'));
      return [button.backgroundColor, button.borderTopWidth, button.borderRadius,
        select.backgroundColor, select.borderRadius, select.appearance];
    });
    assert.deepEqual(styles, ['rgb(18, 52, 86)', '2px', '14px',
      'rgb(250, 250, 250)', '14px', 'none']);
    const layout = await page.evaluate(() => {
      const widget = document.querySelector('.mljar-scenarios');
      widget.style.width = '280px';
      const row = widget.querySelector('.ms-actions').getBoundingClientRect();
      const controls = [...widget.querySelector('.ms-actions').children]
        .map(el => el.getBoundingClientRect());
      const compare = widget.querySelector('.ms-compare').getBoundingClientRect();
      const save = widget.querySelector('[aria-label="Save scenario"]').getBoundingClientRect();
      const loadStyle = getComputedStyle(widget.querySelector('.ms-actions .ms-button'));
      const result = {
        sameRow: controls.every(rect => Math.abs(rect.top - row.top) < 1 && Math.abs(rect.height - row.height) < 1),
        fits: controls.every(rect => rect.right <= row.right + 1),
        primaryRow: save.top === compare.top && Math.abs(save.width + compare.width + 8 - row.width) < 1,
        lightOutline: loadStyle.backgroundColor === 'rgba(0, 0, 0, 0)' && loadStyle.borderTopWidth === '1px',
        noNote: !widget.querySelector('.ms-storage-note')
      };
      widget.style.width = '';
      return result;
    });
    assert.deepEqual(layout, { sameRow: true, fits: true, primaryRow: true, lightOutline: true, noNote: true });
    async function save(name) {
      await page
        .getByRole('button', { name: 'Save scenario', exact: true })
        .click();
      await page.getByRole('textbox', { name: 'Scenario name' }).fill(name);
      await page
        .getByRole('dialog')
        .getByRole('button', { name: 'Save', exact: true })
        .click();
      await page.waitForFunction(
        name =>
          document
            .querySelector('[role="status"]')
            .textContent.includes('Saved “' + name),
        name
      );
    }
    await save('Baseline');
    await page.evaluate(() => {
      window.resultValue = 2000;
    });
    await save('High growth');
    await page.getByRole('button', { name: 'Compare', exact: true }).click();
    await page
      .getByRole('dialog')
      .getByRole('button', { name: 'Compare', exact: true })
      .click();
    await page
      .getByRole('dialog', { name: 'Compare scenarios', exact: true })
      .waitFor();
    assert.equal(
      await page
        .locator('.ms-metrics td')
        .allTextContents()
        .then(v => v.includes('1000') && v.includes('2000')),
      true
    );
    assert.equal(await page.locator('.ms-output-card img').count(), 2);
    const table = page.locator('.ms-dataframe').first();
    await table.getByRole('button', { name: 'Revenue', exact: true }).click();
    assert.equal(
      await table
        .locator('tbody tr')
        .first()
        .locator('td')
        .last()
        .textContent(),
      '1'
    );
    await table.getByRole('button', { name: 'Next', exact: true }).click();
    assert.match(await table.textContent(), /Page 2 of 2/);
    assert.equal(
      await page.evaluate(
        () => requests.filter(r => r.event === 'scenario_load').length
      ),
      0
    );
    await page.setViewportSize({ width: 375, height: 760 });
    assert.equal(
      await page
        .locator('.ms-output-grid')
        .first()
        .evaluate(
          el => getComputedStyle(el).gridTemplateColumns.split(' ').length
        ),
      1
    );
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth
      ),
      true
    );
    await page
      .getByRole('dialog')
      .getByRole('button', { name: 'Close', exact: true })
      .click();
    async function openComparison() {
      await page.getByRole('button', { name: 'Compare', exact: true }).click();
      await page.getByRole('dialog').getByRole('button', { name: 'Compare', exact: true }).click();
      await page.getByRole('dialog', { name: 'Compare scenarios', exact: true }).waitFor();
    }
    await openComparison();
    assert.equal(await page.locator('.ms-outline').evaluate(el => getComputedStyle(el).backgroundColor), 'rgba(0, 0, 0, 0)');
    await page.getByRole('button', { name: 'Close comparison', exact: true }).click();
    await page.waitForFunction(() => !document.querySelector('dialog'));
    await openComparison();
    await page.mouse.click(2, 2);
    await page.waitForFunction(() => !document.querySelector('dialog'));
    await page.reload();
    await page.waitForFunction(() => window.rendered);
    assert.equal(await page.getByRole('combobox').locator('option').count(), 3);
    await page.getByRole('combobox').selectOption('Baseline');
    await page.getByRole('button', { name: 'Load', exact: true }).click();
    await page.waitForFunction(() => requests.length === 1);
    await page.waitForFunction(() =>
      document
        .querySelector('[role="status"]')
        .textContent.startsWith('Inputs loaded')
    );
    assert.equal(
      await page.evaluate(() => 'outputs' in requests[0].snapshot),
      false
    );
    assert.equal(
      await page
        .getByRole('button', { name: 'Save scenario', exact: true })
        .isDisabled(),
      true
    );
    await page.evaluate(() => {
      state.ready = true;
      emit('change:ready');
    });
    await page.waitForFunction(
      () =>
        ![...document.querySelectorAll('button')].find(
          b => b.getAttribute('aria-label') === 'Save scenario'
        ).disabled
    );
    await page.getByRole('button', { name: 'Delete', exact: true }).click();
    await page
      .getByRole('dialog')
      .getByRole('button', { name: 'Delete', exact: true })
      .click();
    await page.waitForFunction(
      () => document.querySelector('select').options.length === 2
    );
    await page.getByRole('textbox', { name: 'Growth', exact: true }).fill('9');
    assert.equal(
      await page
        .getByRole('button', { name: 'Save scenario', exact: true })
        .isDisabled(),
      true
    );
    // Storage scopes isolate independent apps/components in the same browser.
    assert.equal(
      await page.evaluate(async () => {
        const { openStore } = await import('/widget.js');
        const isolated = await openStore('different-notebook');
        const count = (await isolated.list()).length;
        isolated.close();
        return count;
      }),
      0
    );
    assert.deepEqual(errors, []);
    console.log('Scenario browser and execution-bridge checks passed.');
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
