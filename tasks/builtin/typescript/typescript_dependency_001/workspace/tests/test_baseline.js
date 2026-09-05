const assert = require('assert');
const { loadConfig } = require('../src/env_loader');

const raw = '{"port": 8080, "debug": true}';
const cfg = loadConfig(raw);
assert.strictEqual(cfg.port, 8080);
assert.strictEqual(cfg.debug, true);
console.log('Baseline passed');
