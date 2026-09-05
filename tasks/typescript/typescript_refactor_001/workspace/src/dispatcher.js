class Dispatcher {
  constructor(options = {}) {
    this.options = options;
  }

  async dispatch(fn) {
    // Un-refactored direct call
    return await fn();
  }
}

module.exports = { Dispatcher };
