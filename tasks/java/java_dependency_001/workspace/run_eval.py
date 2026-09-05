import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# If mvn is in PATH, run dependency tree validation
if shutil.which("mvn"):
    res = subprocess.run(["mvn", "dependency:tree"], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(res.returncode)

xml_text = Path("pom.xml").read_text(encoding="utf-8")
errors = []

if "<exclusions>" not in xml_text:
    errors.append("Missing <exclusions> tag under dependency.")
if "slf4j-log4j12" not in xml_text:
    errors.append("slf4j-log4j12 is not excluded in pom.xml.")

if errors:
    for e in errors:
        sys.stderr.write(f"Evaluation Error: {e}\n")
    sys.exit(1)

print("Evaluation passed")
sys.exit(0)
