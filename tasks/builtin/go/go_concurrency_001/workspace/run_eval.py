import shutil
import subprocess
import sys
from pathlib import Path

# If go is in PATH and go.mod exists, run full go test with race detector
if shutil.which("go") and Path("go.mod").exists():
    res = subprocess.run(["go", "test", "-race", "./..."], capture_output=True, text=True)
    sys.exit(res.returncode)

# Portable structural AST/code verification
code = Path("src/cache.go").read_text(encoding="utf-8")

errors = []
if "sync" not in code:
    errors.append("Missing 'sync' package import.")
if "RWMutex" not in code and "Mutex" not in code:
    errors.append("Cache struct does not include a sync.RWMutex or sync.Mutex field.")
if "Lock()" not in code and ".Lock" not in code:
    errors.append("Set() does not acquire write lock.")
if "RLock()" not in code and "Lock()" not in code:
    errors.append("Get() does not acquire read lock.")
if "Unlock()" not in code and ".Unlock" not in code:
    errors.append("Locks are not unlocked.")

if errors:
    for e in errors:
        sys.stderr.write(f"Evaluation Error: {e}\n")
    sys.exit(1)

print("Evaluation passed")
sys.exit(0)
