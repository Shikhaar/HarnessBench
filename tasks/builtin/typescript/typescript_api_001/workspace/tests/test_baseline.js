const assert = require('assert');
const { serializeApiResponse } = require('../src/serializer');

// Baseline test: flat object with string and number
const input = {
  user_id: 101,
  first_name: 'John',
};

const output = serializeApiResponse(input);
assert.strictEqual(output.userId, 101);
assert.strictEqual(output.firstName, 'John');
console.log('Baseline test passed');
