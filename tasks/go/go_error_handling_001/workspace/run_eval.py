import shutil
import subprocess
import sys
from pathlib import Path

if shutil.which("go"):
    res = subprocess.run(["go", "test", "./..."], capture_output=True, text=True)
    sys.exit(res.returncode)

code = Path("src/errors.go").read_text(encoding="utf-8")
errors = []

if "ErrNotFound" not in code:
    errors.append("Missing sentinel error ErrNotFound.")
if "ErrUnauthorized" not in code:
    errors.append("Missing sentinel error ErrUnauthorized.")
if "Unwrap()" not in code and "Unwrap ()" not in code:
    errors.append("ApiError does not implement Unwrap() error.")
import re
if not re.search(r'\b(Err|err)\s+error\b', code):
    errors.append("ApiError struct does not contain an underlying error field.")

if errors:
    for e in errors:
        sys.stderr.write(f"Evaluation Error: {e}\n")
    sys.exit(1)

print("Evaluation passed")
sys.exit(0)
