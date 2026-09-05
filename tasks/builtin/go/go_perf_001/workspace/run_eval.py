import shutil
import subprocess
import sys
from pathlib import Path

if shutil.which("go"):
    res = subprocess.run(["go", "test", "./..."], capture_output=True, text=True)
    sys.exit(res.returncode)

code = Path("src/buffer.go").read_text(encoding="utf-8")
errors = []

if "bytes" not in code:
    errors.append("Missing 'bytes' package import.")
if "bytes.Buffer" not in code:
    errors.append("StreamAccumulator does not use bytes.Buffer.")
if ".Reset()" not in code:
    errors.append("Reset() does not call Reset() on the bytes.Buffer.")

if errors:
    for e in errors:
        sys.stderr.write(f"Evaluation Error: {e}\n")
    sys.exit(1)

print("Evaluation passed")
sys.exit(0)
