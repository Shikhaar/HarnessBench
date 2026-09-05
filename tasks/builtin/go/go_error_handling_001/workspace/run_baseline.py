import sys
from pathlib import Path

code = Path("src/errors.go").read_text(encoding="utf-8")
assert "type ApiError struct" in code
assert "func (e *ApiError) Error()" in code
print("Baseline passed")
sys.exit(0)
