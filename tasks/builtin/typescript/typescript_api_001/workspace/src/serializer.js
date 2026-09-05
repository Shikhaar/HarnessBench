function snakeToCamel(str) {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

function serializeApiResponse(data) {
  // BUG: Fails on null or arrays
  if (typeof data !== 'object') {
    return data;
  }

  const result = {};
  for (const [key, value] of Object.entries(data)) {
    const camelKey = snakeToCamel(key);
    result[camelKey] = serializeApiResponse(value);
  }
  return result;
}

module.exports = { serializeApiResponse, snakeToCamel };
