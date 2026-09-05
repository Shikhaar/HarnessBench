const assert = require('assert');
const { loadConfig } = require('./src/env_loader');

// 1. Test trailing comma and comment stripping
const jsonWithComments = `
{
  // Server port configuration
  "port": 5000,
  "service_name": "auth-service",
}
`;

const res = loadConfig(jsonWithComments);
assert.strictEqual(res.port, 5000);
assert.strictEqual(res.service_name, 'auth-service');
assert.strictEqual(res.debug, false); // default

// 2. Test missing port fallback to 3000
const emptyJson = '{}';
const resEmpty = loadConfig(emptyJson);
assert.strictEqual(resEmpty.port, 3000);
assert.strictEqual(resEmpty.debug, false);

console.log('Dep config eval passed');
