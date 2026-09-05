import sys
from pathlib import Path

code = Path("src/buffer.go").read_text(encoding="utf-8")
assert "type StreamAccumulator struct" in code
assert "func NewStreamAccumulator()" in code
assert "func (s *StreamAccumulator) Write" in code
print("Baseline passed")
sys.exit(0)
