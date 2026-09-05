import sys
from pathlib import Path

p_code = Path("payment-api/src/PaymentRequest.java").read_text(encoding="utf-8")
assert "class PaymentRequest" in p_code
assert "getToken()" in p_code
print("Baseline passed")
sys.exit(0)
