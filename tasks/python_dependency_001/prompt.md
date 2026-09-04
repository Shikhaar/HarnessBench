# Dependency Compatibility: Fix collections.Mapping

In `src/sanitizer.py`, the code crashes with:
`AttributeError: module 'collections' has no attribute 'Mapping'`
because in Python 3.10+, abstract collection classes were moved to `collections.abc`.

### Goal:
Update `src/sanitizer.py` to import `Mapping` from `collections.abc` and resolve the compatibility failure while ensuring recursive sanitization functions correctly.
