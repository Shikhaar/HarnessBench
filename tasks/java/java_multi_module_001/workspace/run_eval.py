import shutil
import subprocess
import sys
from pathlib import Path

if shutil.which("javac"):
    res = subprocess.run(["javac", "payment-api/src/PaymentRequest.java", "order-service/src/OrderService.java"], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(res.returncode)

code = Path("order-service/src/OrderService.java").read_text(encoding="utf-8")
errors = []

if "getPaymentToken()" in code:
    errors.append("Still calling obsolete method getPaymentToken().")
if "getToken()" not in code:
    errors.append("OrderService does not call req.getToken().")

if errors:
    for e in errors:
        sys.stderr.write(f"Evaluation Error: {e}\n")
    sys.exit(1)

print("Evaluation passed")
sys.exit(0)
