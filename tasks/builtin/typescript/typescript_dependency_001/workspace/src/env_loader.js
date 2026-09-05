function loadConfig(jsonString) {
  // BUG: Direct JSON.parse fails on trailing commas or comments
  const parsed = JSON.parse(jsonString);
  return parsed;
}

module.exports = { loadConfig };
