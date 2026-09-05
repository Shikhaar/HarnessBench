const assert = require('assert');
const { executeWithRetry } = require('./src/retry');
const { Dispatcher } = require('./src/dispatcher');

async function test() {
  // 1. Verify executeWithRetry handles transient failures
  let attempts = 0;
  const flakyFn = async () => {
    attempts++;
    if (attempts < 3) {
      throw new Error('Transient 503 error');
    }
    return 'recovered';
  };

  const retryRes = await executeWithRetry(flakyFn, { maxRetries: 3, delayMs: 5 });
  assert.strictEqual(retryRes, 'recovered');
  assert.strictEqual(attempts, 3);

  // 2. Verify Dispatcher delegates to retry
  let dAttempts = 0;
  const d = new Dispatcher();
  const dRes = await d.dispatch(async () => {
    dAttempts++;
    if (dAttempts < 2) throw new Error('First try failed');
    return 'dispatcher ok';
  });
  assert.strictEqual(dRes, 'dispatcher ok');
  assert.strictEqual(dAttempts, 2);

  console.log('Refactor eval passed');
}

test();
