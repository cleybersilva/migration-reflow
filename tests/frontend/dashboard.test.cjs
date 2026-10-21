const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.resolve(__dirname, '../../dashboard/app.js'), 'utf8');
const { metrics } = require('../../dashboard/app.js');

test('initial state does not claim 100 percent success', () => {
  assert.deepEqual(metrics({steps: []}), {completed: 0, errors: 0, skipped: 0, total: 0, progress: 0});
});
test('skipped and failed stages do not count as completed', () => {
  assert.deepEqual(metrics({steps: [{status: 'completed'}, {status: 'error'}, {status: 'skipped'}, {status: 'running'}]}),
    {completed: 1, errors: 1, skipped: 1, total: 4, progress: 75});
});
test('frontend uses named SSE listeners, same origin and posts only on a click', async () => {
  class Element {
    constructor() { this.dataset = {}; this.children = []; this.options = []; this.value = ''; this.listeners = {}; }
    set textContent(value) { this.text = value; }
    get textContent() { return this.text; }
    append(...values) { this.children.push(...values); this.options = this.children; }
    replaceChildren(...values) { this.children = values; this.options = values; }
    addEventListener(name, fn) { this.listeners[name] = fn; }
    setAttribute() {}
  }
  const elements = new Map();
  const element = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
  let bootstrap;
  const requests = [];
  const channels = [];
  const snapshot = {revision: 0, active: false, status: 'idle', projects: [], steps: [], logs: []};
  const document = {addEventListener: (_, fn) => { bootstrap = fn; }, getElementById: element,
    querySelector: element, createElement: () => new Element()};
  class Events { constructor(url) { this.url = url; this.listeners = {}; channels.push(this); }
    addEventListener(name, fn) { this.listeners[name] = fn; } }
  const context = {document, location: {protocol: 'http:'}, EventSource: Events, console,
    AbortController, setTimeout, clearTimeout, setInterval: () => {},
    fetch: async (url, options) => { requests.push({url, options}); return {ok: true, json: async () =>
      url === '/api/status' ? {csrf: 'synthetic', projects: ['synthetic'], snapshot,
        ollama: {available: true, model: 'synthetic-model', message: 'fixture'}} : {run_id: 'test'}}; }};
  vm.runInNewContext(source, context);
  await bootstrap();
  assert.equal(requests.filter(r => r.url === '/api/run').length, 0);
  const events = channels[0];
  assert.ok(events.listeners.snapshot && events.listeners.update);
  events.listeners.open(); events.listeners.open();
  assert.equal(requests.filter(r => r.url === '/api/run').length, 0);
  await element('run-btn').listeners.click();
  assert.equal(requests.filter(r => r.url === '/api/run').length, 1);
  assert.equal(requests.at(-2).options.headers['X-Reflow-Token'], 'synthetic');
  assert.ok(requests.every(r => r.url.startsWith('/api/')));
  const running = {...snapshot, revision: 2, active: true, status: 'running', projects: ['synthetic'],
    steps: [{project: 'synthetic', id: 'document', label: 'Documentação', status: 'running', detail: 'Gerando'}]};
  events.listeners.update({data: JSON.stringify({snapshot: running})});
  assert.equal(element('run-btn').disabled, true);
  assert.equal(element('pipeline-status').textContent, 'Em execução');
  assert.equal(element('steps-container').children[0].dataset.state, 'running');
});
