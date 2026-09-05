const assert = require('assert');
const { Dispatcher } = require('../src/dispatcher');

async function run() {
  const d = new Dispatcher();
  const res = await d.dispatch(async () => 'success');
  assert.strictEqual(res, 'success');
  console.log('Baseline passed');
}

run();
