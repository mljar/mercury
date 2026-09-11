const MAX_SCENARIOS = 20;
const MAX_BYTES = 20 * 1024 * 1024;

function text(value) {
  if (value == null) return '—';
  if (Array.isArray(value)) return value.map(text).join(', ');
  if (typeof value === 'object') return String(value.value ?? '—');
  return String(value);
}

function element(tag, className, value) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (value !== undefined) el.textContent = value;
  return el;
}

function button(label, action) {
  const el = element('button', 'ms-button', label);
  el.type = 'button';
  el.addEventListener('click', action);
  return el;
}

export function openStore(scope) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('mercury-scenarios', 1);
    request.onupgradeneeded = () => {
      const store = request.result.createObjectStore('snapshots', {
        keyPath: ['scope', 'name']
      });
      store.createIndex('scope', 'scope');
    };
    request.onerror = () => reject(request.error);
    request.onblocked = () =>
      reject(
        new Error('Close other Mercury tabs to upgrade scenario storage.')
      );
    request.onsuccess = () => {
      const db = request.result;
      db.onversionchange = () => db.close();
      function transaction(mode, action) {
        return new Promise((done, fail) => {
          const tx = db.transaction('snapshots', mode);
          let result;
          let failure;
          tx.oncomplete = () => done(result);
          tx.onerror = () => fail(failure || tx.error);
          tx.onabort = () =>
            fail(
              failure || tx.error || new Error('Storage operation aborted.')
            );
          action(
            tx.objectStore('snapshots'),
            value => {
              result = value;
            },
            error => {
              failure = error;
              tx.abort();
            }
          );
        });
      }
      resolve({
        close: () => db.close(),
        list: () =>
          transaction('readonly', (store, done) => {
            store.index('scope').getAll(scope).onsuccess = event =>
              done(event.target.result.map(item => item.snapshot));
          }),
        save: (snapshot, replace = false) =>
          transaction('readwrite', (store, done, fail) => {
            store.index('scope').getAll(scope).onsuccess = event => {
              const records = event.target.result;
              if (
                !replace &&
                records.some(item => item.name === snapshot.name)
              ) {
                fail(
                  new Error(
                    'A scenario with this name already exists. Choose another name or confirm replacement.'
                  )
                );
                return;
              }
              const remaining = records.filter(
                item => item.name !== snapshot.name
              );
              const bytes = new Blob([JSON.stringify(snapshot)]).size;
              if (
                remaining.length >= MAX_SCENARIOS ||
                bytes + remaining.reduce((n, item) => n + item.bytes, 0) >
                  MAX_BYTES
              ) {
                fail(
                  new Error(
                    'Storage limit reached (20 scenarios or 20 MiB per component). Delete a scenario first.'
                  )
                );
                return;
              }
              store.put({ scope, name: snapshot.name, snapshot, bytes });
            };
          }),
        remove: name =>
          transaction('readwrite', store => store.delete([scope, name]))
      });
    };
  });
}

function compareValue(a, b) {
  if (a == null) return b == null ? 0 : 1;
  if (b == null) return -1;
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  if (a?.type === 'integer' || b?.type === 'integer') {
    try {
      const x = BigInt(a.value ?? a),
        y = BigInt(b.value ?? b);
      return x < y ? -1 : x > y ? 1 : 0;
    } catch {
      /* Mixed value types use their displayed text. */
    }
  }
  return text(a).localeCompare(text(b), undefined, { numeric: true });
}

export function tableView(snapshot) {
  const root = element('div', 'ms-dataframe');
  let page = 0,
    sortColumn = -1,
    direction = 1;
  const pageSize = 10;
  function draw() {
    root.replaceChildren();
    const rows = snapshot.rows.map((row, index) => ({ row, index }));
    if (sortColumn >= 0)
      rows.sort(
        (a, b) => direction * compareValue(a.row[sortColumn], b.row[sortColumn])
      );
    const wrapper = element('div', 'ms-table-scroll');
    wrapper.tabIndex = 0;
    wrapper.setAttribute('aria-label', 'Scenario table');
    const table = element('table', 'ms-table');
    const head = element('thead');
    const tr = element('tr');
    if (snapshot.index)
      tr.append(element('th', '', snapshot.index_name || 'Index'));
    snapshot.columns.forEach((column, index) => {
      const th = element('th');
      th.setAttribute('scope', 'col');
      th.setAttribute(
        'aria-sort',
        sortColumn === index
          ? direction === 1
            ? 'ascending'
            : 'descending'
          : 'none'
      );
      th.append(
        button(
          column +
            (sortColumn === index ? (direction === 1 ? ' ↑' : ' ↓') : ''),
          () => {
            direction = sortColumn === index ? -direction : 1;
            sortColumn = index;
            page = 0;
            draw();
          }
        )
      );
      tr.append(th);
    });
    head.append(tr);
    const body = element('tbody');
    rows
      .slice(page * pageSize, (page + 1) * pageSize)
      .forEach(({ row, index }) => {
        const tr = element('tr');
        if (snapshot.index) tr.append(element('th', '', snapshot.index[index]));
        row.forEach(value => tr.append(element('td', '', text(value))));
        body.append(tr);
      });
    table.append(head, body);
    wrapper.append(table);
    const controls = element('div', 'ms-pagination');
    const pages = Math.max(1, Math.ceil(rows.length / pageSize));
    const previous = button('Previous', () => {
      page--;
      draw();
    });
    previous.disabled = page === 0;
    const next = button('Next', () => {
      page++;
      draw();
    });
    next.disabled = page + 1 >= pages;
    controls.append(
      previous,
      element('span', '', `${rows.length} rows · Page ${page + 1} of ${pages}`),
      next
    );
    root.append(wrapper, controls);
  }
  draw();
  return root;
}

export function comparisonView(snapshots) {
  const root = element('div', 'ms-comparison');
  const wrapper = element('div', 'ms-table-scroll');
  const table = element('table', 'ms-table ms-metrics');
  const head = element('thead');
  const header = element('tr');
  header.append(element('th', '', 'Metric'));
  snapshots.forEach(item => header.append(element('th', '', item.name)));
  head.append(header);
  const body = element('tbody');
  for (const section of ['inputs', 'outputs']) {
    const divider = element('tr', 'ms-section-row');
    const cell = element('th', '', section === 'inputs' ? 'Inputs' : 'Outputs');
    cell.colSpan = snapshots.length + 1;
    divider.append(cell);
    body.append(divider);
    const labels = [
      ...new Set(snapshots.flatMap(item => Object.keys(item[section])))
    ];
    labels.forEach(label => {
      if (
        section === 'outputs' &&
        !snapshots.some(item => item.outputs[label]?.kind === 'scalar')
      )
        return;
      const tr = element('tr');
      tr.append(element('th', '', label));
      const values = snapshots.map(item =>
        section === 'inputs' ? item.inputs[label] : item.outputs[label]?.value
      );
      values.forEach((value, index) => {
        tr.append(
          element(
            'td',
            index && JSON.stringify(value) !== JSON.stringify(values[0])
              ? 'ms-different'
              : '',
            text(value)
          )
        );
      });
      body.append(tr);
    });
  }
  table.append(head, body);
  wrapper.append(table);
  root.append(wrapper);
  const labels = [
    ...new Set(snapshots.flatMap(item => Object.keys(item.outputs)))
  ];
  labels.forEach(label => {
    if (
      !snapshots.some(item =>
        ['table', 'plot'].includes(item.outputs[label]?.kind)
      )
    )
      return;
    root.append(element('h3', '', label));
    const grid = element('div', 'ms-output-grid');
    snapshots.forEach(item => {
      const card = element('section', 'ms-output-card');
      card.append(element('h4', '', item.name));
      const output = item.outputs[label];
      if (output?.kind === 'table') card.append(tableView(output));
      else if (
        output?.kind === 'plot' &&
        output.mime === 'image/png' &&
        /^iVBORw0KGgo[A-Za-z0-9+/=\s]*$/.test(output.data)
      ) {
        const image = element('img');
        image.src = `data:image/png;base64,${output.data}`;
        image.alt = `${label} — ${item.name}`;
        card.append(image);
      } else
        card.append(
          element(
            'p',
            '',
            output?.kind === 'scalar' ? text(output.value) : 'Not available'
          )
        );
      grid.append(card);
    });
    root.append(grid);
  });
  return root;
}

async function render({ model, el }) {
  const root = element('section', 'mljar-scenarios');
  const heading = element('h3', '', 'Scenarios');
  const selector = element('select', 'ms-selector');
  selector.setAttribute('aria-label', 'Saved scenario');
  const selectControl = element('div', 'ms-select-control');
  selectControl.append(selector);
  const status = element('p', 'ms-status');
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  const actions = element('div', 'ms-actions');
  let store,
    scenarios = [],
    pending = false,
    storageError = '';
  let dirty = false;
  let host;
  const requests = new Map();
  const dialogs = new Set();
  const loadButton = button('Load', load);
  const saveButton = button('Save', save);
  saveButton.setAttribute('aria-label', 'Save scenario');
  const compareButton = button('Compare', compare);
  compareButton.classList.add('ms-compare');
  const deleteButton = button('Delete', remove);
  actions.append(selectControl, loadButton, deleteButton);
  const primaryActions = element('div', 'ms-primary-actions');
  primaryActions.append(saveButton, compareButton);
  root.append(heading, actions, primaryActions, status);
  el.append(root);

  function state() {
    const running =
      model.get('running') || host?.dataset.scenarioRunning === 'true';
    const failed = host?.dataset.scenarioFailed === 'true';
    saveButton.disabled =
      !store || pending || running || failed || dirty || !model.get('ready');
    loadButton.disabled = !store || pending || running || !selector.value;
    deleteButton.disabled = !store || pending || !selector.value;
    compareButton.disabled = !store || scenarios.length < 2;
    selector.disabled = pending;
    root.setAttribute('aria-busy', String(pending || !!running));
    if (!pending)
      status.textContent =
        storageError ||
        (failed
          ? 'Execution failed. Re-run the analysis before saving.'
          : dirty
            ? 'Inputs changed. Run the analysis before saving.'
            : model.get('error') || '');
  }
  function ready() {
    if (model.get('ready')) dirty = false;
    state();
  }
  function request(event, payload) {
    return new Promise((resolve, reject) => {
      const id = crypto.randomUUID();
      const timer = setTimeout(() => {
        requests.delete(id);
        reject(
          new Error('The kernel did not respond. Reconnect and try again.')
        );
      }, 30000);
      requests.set(id, { resolve, reject, timer });
      model.send({ event, request_id: id, ...payload });
    });
  }
  function message(content) {
    const waiter = requests.get(content?.request_id);
    if (!waiter) return;
    requests.delete(content.request_id);
    clearTimeout(waiter.timer);
    if (content.event === 'scenario_error')
      waiter.reject(new Error(content.message));
    else waiter.resolve(content);
  }
  async function refresh(selected = selector.value) {
    scenarios = await store.list();
    selector.replaceChildren(element('option', '', 'Select a scenario'));
    selector.firstChild.value = '';
    scenarios.forEach(item => {
      const option = element('option', '', item.name);
      option.value = item.name;
      selector.append(option);
    });
    selector.value = selected;
    state();
  }
  async function operation(fn) {
    pending = true;
    state();
    status.textContent = 'Working…';
    let result;
    try {
      result = await fn();
    } catch (error) {
      result = error.message || 'Scenario storage is unavailable.';
    } finally {
      pending = false;
      state();
    }
    if (result) status.textContent = result;
  }
  function dialog(title, body, acceptLabel) {
    return new Promise(resolve => {
      const dialog = element('dialog', 'mljar-scenarios ms-dialog');
      const isComparison = body.classList.contains('ms-comparison');
      if (isComparison)
        dialog.classList.add('ms-dialog-wide');
      const id = `ms-${crypto.randomUUID()}`;
      const heading = element('h2', '', title);
      heading.id = id;
      dialog.setAttribute('aria-labelledby', id);
      const controls = element('div', 'ms-dialog-actions');
      let accepted = false;
      const dismiss = button(acceptLabel ? 'Cancel' : 'Close', () => dialog.close());
      if (isComparison) dismiss.classList.add('ms-outline');
      controls.append(dismiss);
      if (isComparison) {
        const close = button('×', () => dialog.close());
        close.classList.add('ms-dialog-close');
        close.setAttribute('aria-label', 'Close comparison');
        dialog.append(close);
        const outside = event => {
          const rect = dialog.getBoundingClientRect();
          return event.target === dialog && (
            event.clientX < rect.left || event.clientX > rect.right ||
            event.clientY < rect.top || event.clientY > rect.bottom
          );
        };
        let startedOutside = false;
        dialog.addEventListener('pointerdown', event => {
          startedOutside = outside(event);
        });
        dialog.addEventListener('click', event => {
          if (startedOutside && outside(event)) dialog.close();
          startedOutside = false;
        });
      }
      if (acceptLabel) {
        const accept = () => {
          if (!body.reportValidity || body.reportValidity()) {
            accepted = true;
            dialog.close();
          }
        };
        controls.append(button(acceptLabel, accept));
        if (body.tagName === 'FORM') {
          body.addEventListener('submit', event => {
            event.preventDefault();
            accept();
          });
        }
      }
      dialog.append(heading, body, controls);
      dialogs.add(dialog);
      // Preserve app theme variables inherited from the notebook container.
      (host || el).append(dialog);
      dialog.addEventListener(
        'close',
        () => {
          dialogs.delete(dialog);
          dialog.remove();
          resolve(accepted);
        },
        { once: true }
      );
      dialog.showModal();
    });
  }
  async function save() {
    const form = element('form');
    const name = element('input', 'ms-name');
    name.required = true;
    name.maxLength = 80;
    name.setAttribute('aria-label', 'Scenario name');
    name.placeholder = 'Baseline';
    form.append(name);
    if (!(await dialog('Save scenario', form, 'Save'))) return;
    const label = name.value.trim();
    if (!label) {
      status.textContent = 'Enter a scenario name.';
      return;
    }
    const replace = scenarios.some(item => item.name === label);
    if (
      replace &&
      !(await dialog(
        'Replace scenario?',
        element('p', '', `Replace “${label}” with the current results?`),
        'Replace'
      ))
    )
      return;
    if (saveButton.disabled) return;
    await operation(async () => {
      const reply = await request('scenario_save', { name: label });
      await store.save(reply.snapshot, replace);
      await refresh(label);
      return `Saved “${label}”.`;
    });
  }
  async function load() {
    const scenario = scenarios.find(item => item.name === selector.value);
    if (!scenario) return;
    await operation(async () => {
      const { version, inputs, input_types } = scenario;
      const reply = await request('scenario_load', {
        snapshot: { version, inputs, input_types }
      });
      if (reply.changed) {
        dirty = true;
        return 'Inputs loaded. Results will update with the next execution.';
      }
      return 'These inputs are already selected.';
    });
  }
  async function remove() {
    const name = selector.value;
    if (
      !name ||
      !(await dialog(
        'Delete scenario?',
        element('p', '', `Delete “${name}” from this browser?`),
        'Delete'
      ))
    )
      return;
    await operation(async () => {
      await store.remove(name);
      await refresh('');
    });
  }
  async function compare() {
    await operation(async () => {
      await refresh();
    });
    const choices = element('div', 'ms-choices');
    scenarios.forEach((item, index) => {
      const label = element('label');
      const input = element('input');
      input.type = 'checkbox';
      input.checked = index < 2;
      input.value = item.name;
      label.append(input, document.createTextNode(item.name));
      choices.append(label);
    });
    if (!(await dialog('Choose scenarios to compare', choices, 'Compare')))
      return;
    const selected = [...choices.querySelectorAll('input:checked')].map(input =>
      scenarios.find(item => item.name === input.value)
    );
    if (selected.length < 2 || selected.length > 4) {
      status.textContent = 'Select between two and four scenarios.';
      return;
    }
    await dialog('Compare scenarios', comparisonView(selected));
  }
  function inputChanged(event) {
    if (event.target.closest('.mljar-scenarios')) return;
    dirty = true;
    state();
  }
  selector.addEventListener('change', state);
  model.on('msg:custom', message);
  model.on('change:ready', ready);
  model.on('change:running', state);
  model.on('change:error', state);
  state();
  // Anywidget may render before its output has been attached to the app.
  for (let i = 0; i < 60 && !el.isConnected; i++)
    await new Promise(resolve => requestAnimationFrame(resolve));
  host = el.closest('[data-scenario-notebook]');
  host?.addEventListener('input', inputChanged);
  host?.addEventListener('change', inputChanged);
  host?.addEventListener('mercury:scenario-execution', state);
  const scope = JSON.stringify([
    location.origin,
    host?.dataset.scenarioNotebook || location.pathname,
    model.get('storage_key')
  ]);
  try {
    store = await openStore(scope);
    await refresh();
  } catch (error) {
    store?.close();
    store = undefined;
    storageError = `Could not open scenario storage: ${error.message}. Browser storage must be enabled.`;
    state();
  }
  return () => {
    store?.close();
    dialogs.forEach(dialog => dialog.close());
    requests.forEach(waiter => {
      clearTimeout(waiter.timer);
      waiter.reject(new Error('Scenario view closed.'));
    });
    requests.clear();
    model.off('msg:custom', message);
    model.off('change:ready', ready);
    model.off('change:running', state);
    model.off('change:error', state);
    host?.removeEventListener('input', inputChanged);
    host?.removeEventListener('change', inputChanged);
    host?.removeEventListener('mercury:scenario-execution', state);
    root.remove();
  };
}

export default { render };
