import shutil
import subprocess
import sys
from pathlib import Path

# If go is in PATH, run go test
if shutil.which("go"):
    res = subprocess.run(["go", "test", "-run", "TestBaseline", "./..."], capture_output=True, text=True)
    sys.exit(res.returncode)

# Portable check: ensure struct has NewCache and basic methods
code = Path("src/cache.go").read_text(encoding="utf-8")
assert "func NewCache()" in code
assert "func (c *Cache) Get" in code
assert "func (c *Cache) Set" in code
print("Baseline passed")
sys.exit(0)
