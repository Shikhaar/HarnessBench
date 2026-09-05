import sys
from pathlib import Path

code = Path("src/UserAccount.java").read_text(encoding="utf-8")
assert "class UserAccount" in code
assert "getUsername()" in code
print("Baseline passed")
sys.exit(0)
