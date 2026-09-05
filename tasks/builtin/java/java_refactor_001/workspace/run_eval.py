import shutil
import subprocess
import sys
from pathlib import Path

if shutil.which("javac"):
    res = subprocess.run(["javac", "src/UserAccount.java"], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(res.returncode)

code = Path("src/UserAccount.java").read_text(encoding="utf-8")
errors = []

if "class Builder" not in code:
    errors.append("Missing static class Builder.")
if "builder()" not in code:
    errors.append("Missing static builder() factory method.")
if "IllegalArgumentException" not in code:
    errors.append("Missing validation throwing IllegalArgumentException.")
if "UserAccount build()" not in code and "build()" not in code:
    errors.append("Missing build() method returning UserAccount.")

if errors:
    for e in errors:
        sys.stderr.write(f"Evaluation Error: {e}\n")
    sys.exit(1)

print("Evaluation passed")
sys.exit(0)
