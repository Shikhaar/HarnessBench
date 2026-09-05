const assert = require('assert');
const { serializeApiResponse } = require('./src/serializer');

// 1. Test null handling
const payloadWithNull = {
  account_id: 42,
  deleted_at: null,
};
const resNull = serializeApiResponse(payloadWithNull);
assert.strictEqual(resNull.accountId, 42);
assert.strictEqual(resNull.deletedAt, null);

// 2. Test nested object arrays
const complexPayload = {
  order_id: 999,
  order_items: [
    { item_name: 'Keyboard', unit_price: 50 },
    { item_name: 'Mouse', unit_price: 25 },
  ],
};
const resComplex = serializeApiResponse(complexPayload);
assert.strictEqual(resComplex.orderId, 999);
assert.strictEqual(Array.isArray(resComplex.orderItems), true);
assert.strictEqual(resComplex.orderItems[0].itemName, 'Keyboard');
assert.strictEqual(resComplex.orderItems[0].unitPrice, 50);

console.log('Evaluation test passed');
